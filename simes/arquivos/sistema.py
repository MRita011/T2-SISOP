# -*- coding: utf-8 -*-
"""
Sistema de arquivos simulado (camada 3).

Referência: Silberschatz, 9ª ed., cap. 11 — operações, FCB, tabelas de arquivos abertos,
métodos de acesso, estrutura de diretórios, links e proteção.

O que já vem pronto (FORNECIDO): a criação da raiz, as tabelas e os métodos auxiliares
(nome começando com _). Implementem os métodos marcados com TODO.

=====================================================================================
REGRAS DE CUSTO (iguais para todos os grupos — sigam à risca)
=====================================================================================
Um acesso = um bloco lido ou gravado (use _ler, _escrever e _aplicar; eles contam tudo).

Diretórios: cada diretório ocupa 1 bloco (o bloco 0 do diretório, obtido com
_bloco_do_diretorio). Ler um diretório = 1 leitura desse bloco.

resolver("/a/b/c")   lê os diretórios "/", "/a" e "/a/b" (3 leituras) e devolve o FCB de c.
                     resolver("/") devolve a raiz sem ler nada.
Operações que criam, removem ou alteram uma entrada leem os diretórios do caminho até o
pai (inclusive), exatamente como resolver, e depois:

mkdir(p)             + aloca 1 bloco para o novo diretório, grava o bloco do novo diretório
                       (1 escrita) e o bloco do pai (1 escrita)
create(p, tamanho)   + aloca ceil(tamanho / TAMANHO_BLOCO) blocos (conteúdo não é gravado)
                       e grava o bloco do pai (1 escrita)
open(p, modo, h)     lê os diretórios como resolver; nenhuma escrita
read(h, n)           lê os blocos que contêm os bytes [posição, posição + n), limitados ao
                     tamanho do arquivo; avança a posição; devolve os bytes lidos
write(h, n)          se precisar, estende o arquivo (alocador.estender); grava os blocos que
                     contêm [posição, posição + n); avança a posição; atualiza o tamanho e
                     marca o FCB como sujo. No modo 'a', a escrita começa no fim do arquivo.
seek(h, posicao)     muda a posição; nenhum acesso
close(h)             se o FCB está sujo, grava o bloco do diretório pai (1 escrita) e limpa
                     o "sujo"; atualiza as tabelas
unlink(p)            + grava o bloco do pai (1 escrita). Se o arquivo ficar sem links e
                     ninguém o tiver aberto, libera os blocos; se estiver aberto, a liberação
                     acontece no último close.

Tabelas de arquivos abertos:
- self.tabela_global: dict fcb_id -> EntradaGlobal. Uma entrada por arquivo aberto; o
  contador soma as aberturas de todos os processos. A entrada sai quando o contador zera.
- self.tabelas_processo: dict processo -> {handle: EntradaProcesso}. Uma entrada por
  abertura, com a posição e o modo.

Modos de abertura: 'r' (só leitura), 'w' (só escrita), 'rw' (ambos), 'a' (acréscimo, só
escrita). Ler com um handle sem 'r', ou escrever sem 'w'/'a': ErroSA('EBADF').
Erros: lancem ErroSA com o código adequado (veja estruturas.py).

Ganchos dos módulos (já chamados pelas operações do núcleo, que vocês implementam):
- _verificar_permissao(processo, fcb, modo): no núcleo não faz nada; o M5 implementa.
- _verificar_trava(processo, fcb):            no núcleo não faz nada; o M5 implementa.
  O núcleo deve chamar _verificar_permissao no open e _verificar_trava no read e no write.
"""
import math
from collections import Counter

from simes import parametros as P
from simes.arquivos.estruturas import FCB, EntradaGlobal, EntradaProcesso, ErroSA

MAX_LINKS_SIMBOLICOS = 8


class SistemaArquivos:

    def __init__(self, camada, alocador, bloqueio="consultivo"):
        self.camada = camada
        self.alocador = alocador
        self.bloqueio = bloqueio            # 'consultivo' ou 'mandatorio' (M5)
        self.fcbs = {}
        self._proximo_id = 0
        self.agora_ms = 0.0                 # atualizado pelo simulador antes de cada operação
        self.tabela_global = {}             # fcb_id -> EntradaGlobal
        self.tabelas_processo = {}          # processo -> {handle: EntradaProcesso}
        self.usuarios = {}                  # processo -> nome do usuário (M5); padrão: 'root'
        self.contadores = Counter()         # indicadores extras dos módulos (vão para o CSV)
        self.raiz = self._novo_fcb("/", "diretorio", None)
        self.alocador.alocar(self.raiz, 1)  # a raiz já existe ao "formatar": sem custo

    # ================================================================ FORNECIDO
    def _novo_fcb(self, nome, tipo, pai, processo=None):
        """Cria um FCB (dono = usuário do processo) e o registra em self.fcbs. Não aloca blocos."""
        fcb = FCB(self._proximo_id, nome, tipo, pai, self.agora_ms, self.usuario_de(processo))
        self.fcbs[fcb.id] = fcb
        self._proximo_id += 1
        return fcb

    def usuario_de(self, processo):
        return self.usuarios.get(processo, "root")

    def _ler(self, blocos):
        self.camada.ler(blocos)

    def _escrever(self, blocos):
        self.camada.escrever(blocos)

    def _aplicar(self, extras):
        """Executa a lista de acessos extras devolvida pelo alocador."""
        for tipo, bloco in extras:
            if tipo == "L":
                self._ler([bloco])
            else:
                self._escrever([bloco])

    def _bloco_do_diretorio(self, diretorio):
        """Bloco físico onde está o conteúdo do diretório (já executa os extras do alocador)."""
        bloco, extras = self.alocador.bloco_fisico(diretorio, 0)
        self._aplicar(extras)
        return bloco

    def _ler_diretorio(self, diretorio):
        self._ler([self._bloco_do_diretorio(diretorio)])

    def _gravar_diretorio(self, diretorio):
        self._escrever([self._bloco_do_diretorio(diretorio)])

    def _blocos_do_intervalo(self, fcb, inicio, fim):
        """Blocos físicos que contêm os bytes [inicio, fim) do arquivo (executa os extras)."""
        if fim <= inicio:
            return []
        primeiro = inicio // P.TAMANHO_BLOCO
        ultimo = (fim - 1) // P.TAMANHO_BLOCO
        blocos = []
        for i in range(primeiro, ultimo + 1):
            bloco, extras = self.alocador.bloco_fisico(fcb, i)
            self._aplicar(extras)
            blocos.append(bloco)
        return blocos

    @staticmethod
    def _blocos_necessarios(tamanho):
        return int(math.ceil(tamanho / float(P.TAMANHO_BLOCO)))

    @staticmethod
    def _dividir(caminho):
        if not caminho.startswith("/"):
            raise ErroSA("EINVAL", "o caminho deve ser absoluto: %s" % caminho)
        return [p for p in caminho.split("/") if p]

    def _entrada(self, processo, handle):
        try:
            return self.tabelas_processo[processo][handle]
        except KeyError:
            raise ErroSA("EBADF", "%s não tem o handle %s" % (processo, handle))

    def _liberar_arquivo(self, fcb):
        self.alocador.liberar(fcb)
        del self.fcbs[fcb.id]

    def _verificar_permissao(self, processo, fcb, modo):
        """Gancho do M5. No núcleo, tudo é permitido."""
        return None

    def _verificar_trava(self, processo, fcb):
        """Gancho do M5. No núcleo, travas não existem."""
        return None

    # ============================================================ TODO — núcleo (N3)
    
    def resolver(self, caminho, seguir_simbolico=True):
        partes = self._dividir(caminho)
        atual = self.raiz

        # cada item guarda:
        # nome, se é o último componente original e qual link originou esse caminho
        pendentes = [
            (nome, indice == len(partes) - 1, None)
            for indice, nome in enumerate(partes)
        ]

        links_seguidos = 0

        while pendentes:
            nome, componente_final, origem_link = pendentes.pop(0)

            if atual.tipo != "diretorio":
                raise ErroSA("ENOTDIR", caminho)

            self._ler_diretorio(atual)

            if nome not in atual.entradas:
                # se esse pedaço veio do alvo de um link,
                # então encontrei um link pendente
                if origem_link is not None:
                    self.contadores["links_pendentes"] += 1

                raise ErroSA("ENOENT", caminho)

            encontrado = self.fcbs[atual.entradas[nome]]

            if encontrado.tipo == "simbolico":

                # quando pedirem para não seguir o último link,
                # devolvo o próprio fcb do link
                if not seguir_simbolico and componente_final:
                    return encontrado

                links_seguidos += 1

                # evita ficar preso em uma sequência infinita de links
                if links_seguidos > MAX_LINKS_SIMBOLICOS:
                    raise ErroSA("ELOOP", caminho)

                alvo = self._dividir(encontrado.alvo)

                # os componentes do alvo ficam marcados com o id do link
                novos = [
                    (parte, False, encontrado.id)
                    for parte in alvo
                ]

                pendentes = novos + pendentes

                # como os caminhos simulados são absolutos,
                # começo novamente pela raiz
                atual = self.raiz
            else:
                atual = encontrado

        return atual
    
    # ============================================================ 
    def mkdir(self, processo, caminho):
        partes = self._dividir(caminho)

        if not partes:
            raise ErroSA("EEXIST", caminho)

        nome = partes[-1]

        if len(partes) == 1:
            pai = self.raiz
            self._ler_diretorio(pai)
        else:
            caminho_pai = "/" + "/".join(partes[:-1])
            pai = self.resolver(caminho_pai)

            if pai.tipo != "diretorio":
                raise ErroSA("ENOTDIR", caminho_pai)

            self._ler_diretorio(pai)

        if nome in pai.entradas:
            raise ErroSA("EEXIST", caminho)

        novo = self._novo_fcb(nome, "diretorio", pai.id, processo)

        extras = self.alocador.alocar(novo, 1)
        self._aplicar(extras)

        pai.entradas[nome] = novo.id

        self._gravar_diretorio(novo)
        self._gravar_diretorio(pai)

        return novo
    
    # ============================================================ 
    def create(self, processo, caminho, tamanho):
        if tamanho < 0:
            raise ErroSA("EINVAL", "tamanho inválido")

        partes = self._dividir(caminho)

        if not partes:
            raise ErroSA("EEXIST", caminho)

        nome = partes[-1]

        if len(partes) == 1:
            pai = self.raiz
            self._ler_diretorio(pai)
        else:
            caminho_pai = "/" + "/".join(partes[:-1])
            pai = self.resolver(caminho_pai)

            if pai.tipo != "diretorio":
                raise ErroSA("ENOTDIR", caminho_pai)

            self._ler_diretorio(pai)

        if nome in pai.entradas:
            raise ErroSA("EEXIST", caminho)

        novo = self._novo_fcb(nome, "arquivo", pai.id, processo)

        novo.tamanho = tamanho
        quantidade = self._blocos_necessarios(tamanho)

        extras = self.alocador.alocar(novo, quantidade)
        self._aplicar(extras)

        pai.entradas[nome] = novo.id
        self._gravar_diretorio(pai)

        return novo
    
    # ============================================================ 
    def open(self, processo, caminho, modo, handle):
        if modo not in ("r", "w", "rw", "a"):
            raise ErroSA("EINVAL", "modo inválido: %s" % modo)

        fcb = self.resolver(caminho)

        if fcb.tipo == "diretorio":
            raise ErroSA("EISDIR", caminho)

        self._verificar_permissao(processo, fcb, modo)

        if processo not in self.tabelas_processo:
            self.tabelas_processo[processo] = {}

        if handle in self.tabelas_processo[processo]:
            raise ErroSA("EBADF", "handle já em uso: %s" % handle)

        if fcb.id not in self.tabela_global:
            self.tabela_global[fcb.id] = EntradaGlobal(fcb.id)

        global_ = self.tabela_global[fcb.id]
        global_.contador += 1

        posicao = fcb.tamanho if modo == "a" else 0
        self.tabelas_processo[processo][handle] = EntradaProcesso(fcb.id, modo, posicao)

        return handle

    # ============================================================ 
    def read(self, processo, handle, n):
        if n < 0:
            raise ErroSA("EINVAL", "quantidade inválida")

        entrada = self._entrada(processo, handle)

        if "r" not in entrada.modo:
            raise ErroSA("EBADF", "handle sem permissão de leitura")

        fcb = self.fcbs[entrada.fcb_id]
        self._verificar_trava(processo, fcb)

        inicio = entrada.posicao
        fim = min(inicio + n, fcb.tamanho)

        if fim <= inicio:
            return 0

        blocos = self._blocos_do_intervalo(fcb, inicio, fim)
        self._ler(blocos)

        lidos = fim - inicio
        entrada.posicao = fim

        return lidos
    
    # ============================================================ 
    def write(self, processo, handle, n):
        if n < 0:
            raise ErroSA("EINVAL", "quantidade inválida")

        entrada = self._entrada(processo, handle)

        if entrada.modo not in ("w", "a", "rw"):
            raise ErroSA("EBADF", "handle sem permissão de escrita")

        fcb = self.fcbs[entrada.fcb_id]
        self._verificar_trava(processo, fcb)

        if entrada.modo == "a":
            entrada.posicao = fcb.tamanho

        inicio = entrada.posicao
        fim = inicio + n
        quantidade = self._blocos_necessarios(fim)

        if quantidade > len(fcb.blocos):
            extras = self.alocador.estender(fcb, quantidade - len(fcb.blocos))
            self._aplicar(extras)

        blocos = self._blocos_do_intervalo(fcb, inicio, fim)
        
        if blocos:
            self._escrever(blocos)
            
        entrada.posicao = fim
        fcb.tamanho = max(fcb.tamanho, fim)
        fcb.sujo = True
        return n

    # ============================================================ 
    def seek(self, processo, handle, posicao):
        if posicao < 0:
            raise ErroSA("EINVAL", "posição inválida")

        entrada = self._entrada(processo, handle)
        entrada.posicao = posicao

    # ============================================================ 
    def close(self, processo, handle):
        entrada = self._entrada(processo, handle)
        fcb = self.fcbs[entrada.fcb_id]

        global_ = self.tabela_global[fcb.id]

        if fcb.sujo:
            pai = self.fcbs[fcb.pai]
            self._gravar_diretorio(pai)
            fcb.sujo = False

        del self.tabelas_processo[processo][handle]

        global_.contador -= 1
        
        if global_.contador == 0:
            del self.tabela_global[fcb.id]
            
            if fcb.links == 0:
                self._liberar_arquivo(fcb)

        if not self.tabelas_processo[processo]:
            del self.tabelas_processo[processo]

    # ============================================================ 
    def unlink(self, processo, caminho):
        partes = self._dividir(caminho)
        if not partes:
            raise ErroSA("EPERM", "não é permitido remover a raiz")

        nome = partes[-1]

        if len(partes) == 1:
            pai = self.raiz
            self._ler_diretorio(pai)
        else:
            caminho_pai = "/" + "/".join(partes[:-1])
            pai = self.resolver(caminho_pai)

            if pai.tipo != "diretorio":
                raise ErroSA("ENOTDIR", caminho_pai)
            self._ler_diretorio(pai)

        if nome not in pai.entradas:
            raise ErroSA("ENOENT", caminho)

        fcb_id = pai.entradas[nome]
        fcb = self.fcbs[fcb_id]

        del pai.entradas[nome]
        fcb.links -= 1

        self._gravar_diretorio(pai)

        if fcb.links == 0 and fcb.id not in self.tabela_global:
            self._liberar_arquivo(fcb)

    # ======================================================== TODO — módulo M4
    def link(self, processo, existente, novo):
        """Cria um hard link para um arquivo que já existe."""

        # primeiro encontro o arquivo que vai receber outro nome
        fcb = self.resolver(existente)

        # hard link para diretório não é permitido
        if fcb.tipo == "diretorio":
            raise ErroSA("EPERM", existente)

        # separo o caminho novo para encontrar o diretório pai
        partes = self._dividir(novo)

        # não dá para substituir a raiz por um link
        if not partes:
            raise ErroSA("EEXIST", novo)

        nome = partes[-1]

        # se o novo nome vai ficar direto na raiz,
        # preciso ler a raiz porque ela é o diretório pai
        if len(partes) == 1:
            pai = self.raiz
            self._ler_diretorio(pai)

        else:
            caminho_pai = "/" + "/".join(partes[:-1])
            pai = self.resolver(caminho_pai)

            # confere se o caminho realmente terminou em um diretório
            if pai.tipo != "diretorio":
                raise ErroSA("ENOTDIR", caminho_pai)

            # lê o próprio diretório pai antes de mexer na entrada
            self._ler_diretorio(pai)

        # não posso criar outro nome se ele já existe nesse diretório
        if nome in pai.entradas:
            raise ErroSA("EEXIST", novo)

        # os dois nomes vão apontar para o mesmo fcb
        pai.entradas[nome] = fcb.id

        # aumenta a quantidade de hard links desse arquivo
        fcb.links += 1

        # como alterei o conteúdo do diretório, preciso gravar ele
        self._gravar_diretorio(pai)

        return fcb

    def symlink(self, processo, alvo, caminho):
        """Cria um link simbólico apontando para outro caminho."""

        # separo o caminho onde o link vai ser criado
        partes = self._dividir(caminho)

        # não dá para criar um link no lugar da raiz
        if not partes:
            raise ErroSA("EEXIST", caminho)

        nome = partes[-1]

        # se vai ser criado direto na raiz, ela é o diretório pai
        if len(partes) == 1:
            pai = self.raiz
            self._ler_diretorio(pai)
        else:
            caminho_pai = "/" + "/".join(partes[:-1])
            pai = self.resolver(caminho_pai)

            # o pai precisa ser um diretório
            if pai.tipo != "diretorio":
                raise ErroSA("ENOTDIR", caminho_pai)

            # preciso ler o diretório antes de alterar as entradas
            self._ler_diretorio(pai)

        # não posso criar se já existir alguma entrada com esse nome
        if nome in pai.entradas:
            raise ErroSA("EEXIST", caminho)

        # o link simbólico tem seu próprio fcb
        novo = self._novo_fcb(nome, "simbolico", pai.id, processo)

        # guardo somente o caminho para onde ele aponta
        novo.alvo = alvo

        # adiciono o novo link dentro do diretório
        pai.entradas[nome] = novo.id

        # não tem bloco de dados para alocar,
        # só preciso gravar a alteração feita no diretório pai
        self._gravar_diretorio(pai)

        return novo

    def percorrer(self, processo, caminho):
        """Percorre a árvore e conta diretórios, arquivos, ciclos e links pendentes."""

        # guarda os diretórios em que eu já entrei nessa travessia
        visitados = set()

        def visitar(fcb):

            # se for um diretório, preciso verificar se já passei por ele
            if fcb.tipo == "diretorio":

                # se já visitei, achei um ciclo e não desço de novo
                if fcb.id in visitados:
                    self.contadores["ciclos_detectados"] += 1
                    return

                visitados.add(fcb.id)
                self.contadores["percorrer_diretorios"] += 1

                # cada diretório visitado custa uma leitura
                self._ler_diretorio(fcb)

                # percorro todas as entradas que existem dentro dele
                for nome, fcb_id in list(fcb.entradas.items()):
                    filho = self.fcbs[fcb_id]

                    # diretório normal
                    if filho.tipo == "diretorio":
                        visitar(filho)

                    # arquivo normal
                    elif filho.tipo == "arquivo":
                        self.contadores["percorrer_arquivos"] += 1

                    # link simbólico precisa tentar resolver o alvo
                    elif filho.tipo == "simbolico":
                        antes = self.contadores["links_pendentes"]

                        try:
                            alvo = self.resolver(filho.alvo)

                        except ErroSA:
                            # se o resolver ainda não contou,
                            # é porque o próprio alvo direto não existe
                            if self.contadores["links_pendentes"] == antes:
                                self.contadores["links_pendentes"] += 1

                            continue

                        # a regra pede para seguir links simbólicos para diretórios
                        if alvo.tipo == "diretorio":
                            visitar(alvo)

            # se o próprio caminho inicial for um arquivo
            elif fcb.tipo == "arquivo":
                self.contadores["percorrer_arquivos"] += 1

        # resolvo o ponto onde a travessia vai começar
        inicio = self.resolver(caminho)

        visitar(inicio)

    # ======================================================== TODO — módulo M5
    # Regras do M5 (implementem também os ganchos _verificar_permissao e _verificar_trava,
    # sobrescrevendo-os aqui ou numa subclasse):
    #
    # _verificar_permissao(processo, fcb, modo) — chamado no open. Permissão exigida:
    #   'r' para o modo 'r'; 'w' para 'w' e 'a'; 'r' e 'w' para 'rw'.
    #   - usuário root: sempre permitido (conte 1 em contadores['verificacoes']);
    #   - se a ACL do arquivo tem uma entrada para o usuário, vale a PRIMEIRA entrada dele
    #     (some em 'verificacoes' a posição da entrada na lista, começando em 1);
    #   - senão, valem os bits: os do dono, se o usuário for o dono; senão, os de "outros"
    #     (grupos não são simulados). Some len(acl) + 1 em 'verificacoes';
    #   - negado: some 1 em contadores['negados'] e lance ErroSA('EACCES').
    #
    # _verificar_trava(processo, fcb) — chamado no read e no write. Se outro processo
    #   detém a trava do arquivo:
    #   - bloqueio 'consultivo': a operação segue; some 1 em 'violacoes_consultivo';
    #   - bloqueio 'mandatorio': some 1 em 'bloqueados_mandatorio' e lance ErroSA('EBUSY').
    # O close libera a trava se o processo que fecha for o dono dela.
    def usuario(self, processo, nome):
        """Associa o processo a um usuário (nenhum acesso ao disco)."""
        raise NotImplementedError("TODO (M5): usuario")

    def chmod(self, processo, caminho, permissoes):
        """Lê os diretórios até o arquivo; só o dono ou root (senão EPERM); grava o bloco do
        pai (1 escrita). permissoes em octal, como texto (ex.: '640')."""
        raise NotImplementedError("TODO (M5): chmod")

    def setacl(self, processo, caminho, usuario, permissoes):
        """Como o chmod, mas acrescenta (ou substitui) a entrada (usuario, 'rwx') na ACL."""
        raise NotImplementedError("TODO (M5): setacl")

    def lock(self, processo, handle):
        """Trava exclusiva do arquivo inteiro. Se outro processo detém a trava: EBUSY
        (conte 'travas_negadas'); senão conte 'travas_concedidas'."""
        raise NotImplementedError("TODO (M5): lock")

    def unlock(self, processo, handle):
        raise NotImplementedError("TODO (M5): unlock")
