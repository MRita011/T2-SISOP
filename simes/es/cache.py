# -*- coding: utf-8 -*-
"""
Módulo M1 — cache de blocos (buffer cache).

Referência: Silberschatz, 9ª ed., 13.4.3 (Caching) e 12.6 (Efficiency and Performance) — pesquisa.

Implementem CacheLRU e CacheFIFO com a interface abaixo. O simulador de E/S chama:

    ler(bloco) -> bool
        True se o bloco está na cache (acerto). Num acerto, a LRU atualiza a recência;
        a FIFO não muda nada.
    inserir(bloco) -> list[int]
        Chamado depois de uma falta de leitura, quando o bloco chega do disco. Se a cache
        estiver cheia, expulsa uma vítima (LRU: a usada há mais tempo; FIFO: a que entrou
        primeiro). Devolve os blocos SUJOS expulsos, que o simulador vai gravar no disco.
    escrever(bloco) -> list[int]
        Escrita do usuário. Coloca (ou atualiza) o bloco na cache e devolve a lista de blocos
        que precisam ser gravados no disco AGORA:
          write-through: o próprio bloco (+ sujos expulsos, que não existem nesta política);
          write-back:    só os blocos sujos expulsos; o bloco escrito fica marcado como sujo.
        Uma escrita conta como acesso para a LRU.
    sincronizar() -> list[int]
        Gravação periódica (a cada INTERVALO_SYNC_MS): devolve todos os blocos sujos e os
        marca como limpos.
    sujos() -> int
        Quantos blocos estão sujos agora (usado para medir a perda numa queda de energia).

Política de escrita: 'write-through' ou 'write-back'.
"""

from collections import OrderedDict

class Cache:
    nome = "?"

    def __init__(self, capacidade, escrita="write-back"):
        if escrita not in ("write-through", "write-back"):
            raise ValueError("escrita deve ser 'write-through' ou 'write-back'")

        self.capacidade = capacidade
        self.escrita = escrita

    def ler(self, bloco):
        raise NotImplementedError

    def inserir(self, bloco):
        raise NotImplementedError

    def escrever(self, bloco):
        raise NotImplementedError

    def sincronizar(self):
        raise NotImplementedError

    def sujos(self):
        raise NotImplementedError

class CacheLRU(Cache):
    nome = "LRU"

    def __init__(self, capacidade, escrita="write-back"):
        super().__init__(capacidade, escrita)

        # bloco é true se sujo, false se limpo
        # o primeiro elemento é o que foi menos usado recentemente (e o ultimo é o contrario)
        self.blocos = OrderedDict()

    def ler(self, bloco):
        if bloco not in self.blocos:
            return False

        # um acerto atualiza recencia do bloco e move ele pro final da lista
        self.blocos.move_to_end(bloco)

        return True

    def inserir(self, bloco):
        expulsos_sujos = []

        # se o bloco ja estiver na cache, ele nao é expulso (mesmo estando sujo)
        if bloco in self.blocos:
            self.blocos.move_to_end(bloco)
            return expulsos_sujos
        
        # se o cache nao tiver capacidade, nao é possivel inserir o bloco (e tambem nao da pra expulsar ninguem)
        if self.capacidade <= 0:
            return expulsos_sujos

        # se estiver cheia, o bloco menos usado recentemente é expulso
        if len(self.blocos) >= self.capacidade:
            vitima, sujo = self.blocos.popitem(last=False)

            if sujo:
                expulsos_sujos.append(vitima)

        # bloco que vem de uma leitura do disco sempre entra limpo
        self.blocos[bloco] = False

        return expulsos_sujos

    def escrever(self, bloco):
        gravar_agora = []

        # cache com capacidade zero:
        # o bloco não pode permanecer armazenado
        if self.capacidade <= 0:
            return [bloco]

        # se o bloco ainda não está na cache, pode ser necessário expulsar a vítima LRU
        if bloco not in self.blocos:
            if len(self.blocos) >= self.capacidade:
                vitima, sujo = self.blocos.popitem(last=False)

                if sujo:
                    gravar_agora.append(vitima)

            self.blocos[bloco] = False

        # escrita conta como acesso na LRU
        self.blocos.move_to_end(bloco)

        if self.escrita == "write-through":
            # vai imediatamente para o disco e permanece limpa
            self.blocos[bloco] = False
            gravar_agora.append(bloco)

        else:
            # write-back: fica sujo na cache
            self.blocos[bloco] = True

        return gravar_agora

    def sincronizar(self):
        gravar = []

        for bloco in self.blocos:
            if self.blocos[bloco]:
                gravar.append(bloco)
                self.blocos[bloco] = False

        return gravar

    def sujos(self):
        return sum(
            1
            for sujo in self.blocos.values()
            if sujo
        )

class CacheFIFO(Cache):
    nome = "FIFO"

    def __init__(self, capacidade, escrita="write-back"):
        super().__init__(capacidade, escrita)

        # na FIFO, a ordem representa a ordem de entrada
        # ler ou escrever um bloco já existente não altera essa ordem
        self.blocos = OrderedDict()

    def ler(self, bloco):
        return bloco in self.blocos

    def inserir(self, bloco):
        expulsos_sujos = []

        if bloco in self.blocos:
            return expulsos_sujos

        if self.capacidade <= 0:
            return expulsos_sujos

        # remove o bloco que entrou primeiro
        if len(self.blocos) >= self.capacidade:
            vitima, sujo = self.blocos.popitem(last=False)

            if sujo:
                expulsos_sujos.append(vitima)

        # bloco vindo do disco entra limpo
        self.blocos[bloco] = False

        return expulsos_sujos

    def escrever(self, bloco):
        gravar_agora = []

        if self.capacidade <= 0:
            return [bloco]

        # só altera a ordem se o bloco ainda não existir
        if bloco not in self.blocos:
            if len(self.blocos) >= self.capacidade:
                vitima, sujo = self.blocos.popitem(last=False)

                if sujo:
                    gravar_agora.append(vitima)

            self.blocos[bloco] = False

        if self.escrita == "write-through":
            self.blocos[bloco] = False
            gravar_agora.append(bloco)

        else:
            self.blocos[bloco] = True

        return gravar_agora

    def sincronizar(self):
        gravar = []

        for bloco in self.blocos:
            if self.blocos[bloco]:
                gravar.append(bloco)
                self.blocos[bloco] = False

        return gravar

    def sujos(self):
        return sum(
            1
            for sujo in self.blocos.values()
            if sujo
        )

CACHES = {"LRU": CacheLRU,"FIFO": CacheFIFO}

def criar_cache(nome, capacidade, escrita):
    try:
        return CACHES[nome](capacidade, escrita)
    except KeyError:
        raise ValueError("cache desconhecida: %s" % nome)