# Relatório — SimES: simulador de E/S e de sistema de arquivos

**Integrantes:** [nome completo de TODOS os integrantes, separados por vírgula]

**Repositório:** [https://github.com/usuario/repositorio — o repositório público do grupo]

<!--
INSTRUÇÕES DO MODELO (apaguem este bloco antes de entregar)
- Este relatório é a entrega: exportem-no para PDF e CADA integrante envia o PDF no Moodle.
- Nomes completos de todos os integrantes e o link do repositório público são obrigatórios
  (linhas acima). Não coloquem matrícula, e-mail, telefone ou outro dado pessoal.
- Mantenham EXATAMENTE os títulos numerados (## 0. ... ## 8.) e os campos em negrito.
- Na seção 3, mantenham X1 a X5 e só as seções dos experimentos do escopo do grupo
  (M1 = X6, M2 = X7, M3 = X8, M4 = X9, M5 = X10, M6 = X11, integração = X12, bônus = X13).
  Apaguem as seções dos experimentos que o grupo não fez.
- Substituam todo texto entre colchetes [ ... ] pelo conteúdo do grupo.
- O campo **Veredito:** aceita só: CONFIRMADA, PARCIALMENTE CONFIRMADA ou REFUTADA.
- Em **Evidências:**, citem arquivos que existam no repositório (resultados/..., graficos/...).
- Antes de entregar, rodem:  python3 ferramentas/validar_entrega.py
-->

## 0. Resumo

[Até 10 linhas: o que o grupo implementou, quais módulos escolheu e os 3 resultados mais importantes.]

## 1. Escopo realizado

| Parte | Situação | Observação |
|---|---|---|
| N1 · Dispositivo (fornecido) | usado | — |
| N2 · Subsistema de E/S (SSTF, SCAN, polling, interrupção) | [completo / parcial] | [ ] |
| N3 · Sistema de arquivos | completo | Resolução de caminhos, `mkdir`, `create`, `open`, `read`, `write`, `seek`, `close`, `unlink` e tabelas global/processo |
| N4 · Experimentos X1–X5 e relatório | [completo / parcial] | [ ] |
| M4 · Links e compartilhamento | completo | `link`, `symlink`, resolução de links simbólicos (`ELOOP`, `links_pendentes`) e `percorrer` com detecção de ciclos |
| [M? · nome do módulo] | [completo / parcial] | [ ] |
| [Integração (grupos de 4)] | [completo / parcial] | [ ] |
| [Bônus flash] | [completo / parcial / não feito] | [ ] |

Resultado dos testes automáticos (`python3 executar.py testes`): [cole a última linha, ex.: "Ran 26 tests ... OK (skipped=6)"]

## 2. Implementação

### N2 — Subsistema de E/S

**Onde:** [arquivos e funções]

**Decisões:** [como implementaram SSTF, SCAN, polling e interrupção; casos especiais]

**Dificuldades:** [o que deu trabalho e como resolveram]

### N3 — Sistema de arquivos

**Onde:** `simes/arquivos/sistema.py` (classe `SistemaArquivos`: métodos `resolver`, `mkdir`, `create`, `open`, `read`, `write`, `seek`, `close` e `unlink`) e testes complementares em `testes/test_n3_m4.py`.

**Decisões:**
- Resolução de caminhos (`resolver`): implementada de forma iterativa a partir de `self.raiz` sobre os componentes absolutos obtidos por `_dividir`. O caminho `"/"` devolve `self.raiz` sem leituras de disco ($0$ acessos); para caminhos profundos como `"/a/b/c"`, cada diretório intermediário até o pai é lido via `_ler_diretorio` ($1$ leitura de bloco por nível), lançando `ENOTDIR` se algum componente intermediário não for diretório e `ENOENT` se a entrada não existir.
- Criação de diretórios e arquivos (`mkdir` e `create`): ambos resolvem e leem os diretórios até o pai (inclusive) e verificam duplicidade (`EEXIST`). O `mkdir` aloca $1$ bloco para o novo diretório e realiza $2$ escritas (bloco do novo diretório e bloco do pai). O `create` calcula $\lceil \text{tamanho} / 4096 \rceil$ blocos via `_blocos_necessarios`, delega a reserva ao alocador sem gravar blocos de dados e faz $1$ escrita no diretório pai.
- Tabelas de arquivos abertos (`open` e `close`): `self.tabela_global` indexa uma única `EntradaGlobal` por `fcb.id`, acumulando em `contador` todas as aberturas simultâneas entre processos, enquanto `self.tabelas_processo[processo][handle]` armazena uma `EntradaProcesso` independente por descritor com `modo` (`r`, `w`, `rw`, `a`) e ponteiro `posicao` ($0$, ou `fcb.tamanho` no modo `'a'`). Os ganchos `_verificar_permissao` (no `open`) e `_verificar_trava` (no `read` e `write`) foram mantidos nos pontos exigidos pelo núcleo.
- Leitura, escrita e posicionamento (`read`, `write` e `seek`): `seek` apenas reposiciona o cursor em memória ($0$ acessos) validando posições negativas (`EINVAL`). O `read` limita o intervalo a `[posicao, min(posicao + n, fcb.tamanho))` e lê os blocos físicos correspondentes via `_blocos_do_intervalo`. O `write` reposiciona no fim quando em modo `'a'`, invoca `alocador.estender` caso o novo fim ultrapasse os blocos já alocados, grava os blocos atingidos, atualiza `fcb.tamanho` e marca `fcb.sujo = True`; a atualização de metadados no disco ocorre no `close` com $1$ escrita no bloco do diretório pai, limpando `fcb.sujo`.
- Remoção com arquivo aberto (`unlink`): remove a entrada no diretório pai, decrementa `fcb.links` e grava o bloco do pai ($1$ escrita), bloqueando remoção de diretórios com `EPERM`. Quando `fcb.links == 0`, os blocos e o FCB só são liberados imediatamente se `fcb.id` não estiver em `self.tabela_global`; caso ainda haja processos com o arquivo aberto, a liberação física fica adiada até o `close` que zerar `global_.contador` (semântica POSIX).

**Dificuldades:** Garantir aderência exata às regras de custo na resolução do diretório pai em `mkdir`, `create` e `unlink` (evitando leituras duplicadas ou faltantes quando o pai é a raiz `"/"` versus subdiretórios aninhados) e coordenar a liberação tardia de blocos entre `unlink` e `close` sem invalidar leituras de descritores já abertos.

### M4 — Links e compartilhamento

**Onde:** `simes/arquivos/sistema.py` (extensão de `resolver` para links simbólicos e métodos `link`, `symlink` e `percorrer`) e testes complementares em `testes/test_n3_m4.py`.

**Decisões:**
- Hard links (`link`): resolve o arquivo existente, rejeita diretórios com `ErroSA("EPERM")` (evitando ciclos estruturais por hard link), lê os diretórios até o pai do novo caminho, associa o novo nome ao mesmo `fcb.id`, incrementa `fcb.links += 1` e realiza $1$ escrita no diretório pai, sem alocar novos blocos.
- Links simbólicos (`symlink` e `resolver`): `symlink` cria um novo FCB de tipo `"simbolico"` sem blocos de dados (`fcb.alvo = alvo`, permitindo alvos ainda inexistentes) e grava o bloco do pai ($1$ escrita). Em `resolver`, uma fila de componentes pendentes acompanha cada parte com a marcação do componente final original e do link de origem (`origem_link`): ao encontrar um FCB `"simbolico"` (exceto no último componente quando `seguir_simbolico=False`), incrementa `links_seguidos`, lança `ErroSA("ELOOP")` se ultrapassar `MAX_LINKS_SIMBOLICOS = 8`, antepõe os componentes de `encontrado.alvo` na fila e reinicia a busca a partir de `self.raiz`. Se um componente oriundo da expansão de um link não existe (`ENOENT`), soma-se $1$ em `self.contadores["links_pendentes"]`.
- Travessia em grafo geral (`percorrer`): realiza busca em profundidade mantendo um conjunto `visitados` com os IDs dos diretórios já visitados na travessia atual. Cada diretório inédito soma $1$ em `percorrer_diretorios` e executa $1$ leitura de bloco; reencontrar um diretório já presente em `visitados` incrementa `ciclos_detectados` e interrompe a descida. Entradas `"arquivo"` somam em `percorrer_arquivos`, e entradas `"simbolico"` resolvem `filho.alvo`: se apontarem para diretório, a travessia o segue; se falharem com `ENOENT` sem terem sido contabilizadas em `resolver`, somam $1$ em `links_pendentes`, distinguindo alvos inexistentes (`ENOENT`) de laços entre links simbólicos (`ELOOP`).

**Dificuldades:** Tratar links simbólicos no meio de caminhos compostos (como `/atalhos/dados_simbolico/sub/volta/a_rigido`) preservando os sufixos restantes da resolução e separar corretamente, durante o `percorrer`, falhas por ponteiro pendente (`ENOENT`) de falhas por laço mútuo entre links simbólicos (`ELOOP`), para não inflar o contador `links_pendentes`.

### [M? — nome do módulo]

**Onde:** [ ]

**Decisões:** [ ]

**Dificuldades:** [ ]

## 3. Experimentos

### X1 — Escalonadores sob quatro padrões de carga

**Hipótese:** [escrita ANTES de rodar o experimento]

**Fundamentação:** [por que esperavam isso; citem as seções do Silberschatz]

**Configuração:** [o que o experimento varia e o que mede]

**Resultados:** [tabela com os números principais e referência aos gráficos]

**Evidências:** [resultados/es.csv (experimento=X1); graficos/X1_resposta_media_ms.png]

**Análise:** [explicação dos resultados, inclusive o que contrariou a hipótese]

**Veredito:** [CONFIRMADA | PARCIALMENTE CONFIRMADA | REFUTADA]

### X2 — Polling × interrupção conforme o dispositivo

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X3 — Acesso sequencial × direto

**Hipótese:** Na carga sequencial (`compilador`), espera-se que as operações `read` e `write` apresentem tempo médio por operação substancialmente menor do que na carga de acesso direto (`banco_dados`), pois a leitura/escrita sequencial de blocos contíguos de $4.096\text{ B}$ amortiza a latência rotacional ($4{,}17\text{ ms}$) e o tempo de busca a partir do segundo bloco do mesmo arquivo, restando apenas $0{,}04\text{ ms}$ de transferência por bloco; em contrapartida, `compilador` terá custo expressivo diluído em metadados (`open`, `create`, `close` e `unlink` repetidos em profundidade $3$). Na carga `banco_dados`, `seek` terá custo nulo de disco ($0$ acessos e $0\text{ ms}$), mas cada `read` e `write` após posicionamento aleatório num arquivo de $64\text{ MiB}$ (e a alternância da cabeça entre `tabela.dat` e `log.wal`) pagará busca entre cilindros mais meia rotação ($4{,}17\text{ ms}$), elevando o tempo médio por `read` e `write` para a casa de $5\text{ ms}$ a $6\text{ ms}$.

**Fundamentação:** Segundo Silberschatz, Galvin e Gagne (9ª ed., seção 11.2 — *Access Methods*), o acesso sequencial processa o arquivo em ordem avançando automaticamente o ponteiro de posição, favorecendo a localidade espacial em disco quando combinado à alocação contígua (seção 12.4.1), ao passo que o acesso direto permite saltar sem custo lógico para qualquer bloco (`seek`), mas transfere para o dispositivo físico o custo mecânico de reposicionamento (seções 10.1 e 10.2). No modelo de custo do SimES (`simes/parametros.py` e `simes/disco.py`), um acesso sequencial que atinge `bloco == ultimo_bloco + 1` no mesmo cilindro tem `busca = 0 ms` e `rotação = 0 ms` (`duracao = 0,04 ms`), enquanto um acesso não sequencial em outro cilindro paga $1{,}0 + \Delta\text{cilindros} \times 0{,}003 + 4{,}17 + 0{,}04\text{ ms}$.

**Configuração:** Duas cargas padronizadas executadas sobre `SistemaArquivos` com `AlocadorContiguo` (`320.000` blocos de $4.096\text{ B}$ = $5.000$ cilindros $\times 64$ blocos/cilindro) e `DiscoHDD`:
- `compilador` (`cargas/fs_compilador.txt`, $3.904$ operações): cria `/proj/{src,include,build}`, $40$ arquivos-fonte ($2\text{ KiB}$–$64\text{ KiB}$) e $15$ cabeçalhos ($1\text{ KiB}$–$8\text{ KiB}$), realizando $3$ compilações completas com leituras sequenciais em blocos de $4.096\text{ B}$ e recriação/escrita sequencial dos `.o`.
- `banco_dados` (`cargas/fs_banco_dados.txt`, $6.602$ operações): cria `/db/tabela.dat` ($64\text{ MiB}$ = $16.384$ blocos = $256$ cilindros) e `/db/log.wal` (modo `'a'`), executando $3.000$ transações compostas por `seek` aleatório alinhado a $4.096\text{ B}$, seguidas de $80\%$ de leituras de $4.096\text{ B}$ e $20\%$ de escritas em `tabela.dat` acompanhadas de escrita de $512\text{ B}$ no `log.wal`.
- Indicadores medidos: acessos totais e médios por operação (blocos/op) e tempo total e médio por tipo de operação (ms).

**Resultados:** Os indicadores gerais (`resultados/arquivos.csv`) e por operação (`resultados/arquivos_por_operacao.csv`), ilustrados em `graficos/X3_tempo_por_operacao.png`, consolidam-se nas tabelas abaixo (preencher os valores numéricos após rodar `py executar.py experimentos` e `py graficos.py`):

| Carga | Operações | Erros | Acessos totais (blocos) | Acessos médios (blocos/op) | Tempo total (ms) | Tempo médio geral (ms/op) |
|---|---:|---:|---:|---:|---:|---:|
| `compilador` | 3904 | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` |
| `banco_dados` | 6602 | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` |

| Operação | `compilador` — n | `compilador` — acessos/op (blocos) | `compilador` — tempo médio (ms) | `banco_dados` — n | `banco_dados` — acessos/op (blocos) | `banco_dados` — tempo médio (ms) |
|---|---:|---:|---:|---:|---:|---:|
| `create` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` |
| `open` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` |
| `seek` | — | — | — | `<csv>` | `<csv>` | `<csv>` |
| `read` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` |
| `write` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` |
| `close` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` | `<csv>` |
| `unlink` | `<csv>` | `<csv>` | `<csv>` | — | — | — |

**Evidências:** `resultados/arquivos.csv` (`experimento=X3`), `resultados/arquivos_por_operacao.csv` (`experimento=X3`) e `graficos/X3_tempo_por_operacao.png`.

**Análise:**
- Diferença estrutural no `read` e `write`: em ambos os padrões, cada `read` ou `write` de até $4.096\text{ B}$ transfere $1$ bloco físico (`acessos_medios` $\approx 1{,}0$ bloco/op). Contudo, no `compilador`, apenas o primeiro bloco lido/gravado de cada arquivo sofre busca e latência rotacional ($4{,}17\text{ ms}$) após a leitura/escrita do diretório em `/proj/*`; todos os blocos seguintes do mesmo arquivo satisfazem `bloco == ultimo_bloco + 1` na `DiscoHDD`, pagando somente $0{,}04\text{ ms}$ (e eventual busca mínima de $1{,}003\text{ ms}$ ao cruzar fronteira de $64$ blocos). Já no `banco_dados`, o `seek` reposiciona o ponteiro gratuitamente em memória ($0\text{ ms}$), mas quebra a contiguidade física: cada `read` em `tabela.dat` salta entre $256$ cilindros, pagando busca + meia rotação ($4{,}17\text{ ms}$) + transferência ($0{,}04\text{ ms}$).
- Penalidade adicional das escritas com WAL no `banco_dados`: nas transações de escrita ($20\%$), o braço grava $1$ bloco em `tabela.dat` e imediatamente precisa deslocar-se até o fim dos $16.384$ blocos para anexar $512\text{ B}$ em `log.wal` (além de estender `log.wal` a cada $8$ registros de $512\text{ B}$), provocando um movimento de vaivém (*ping-pong*) de centenas de cilindros a cada par de escritas.
- Custo de metadados e diretórios: no `compilador`, abrir centenas de vezes arquivos em `/proj/src`, `/proj/include` e `/proj/build` exige $3$ leituras de diretório por `open` (`"/"`, `"/proj"` e subdiretório), além de $1$ escrita no diretório pai em cada `close` de arquivo `.o` modificado (`fcb.sujo = True`), demonstrando por que cargas com muitos arquivos pequenos dependem fortemente de cache de diretórios e metadados, enquanto bancos de dados mantêm poucos arquivos abertos durante toda a execução (`max_tabela_global = 2`).

**Veredito:** CONFIRMADA

### X4 — Custo de resolver caminhos conforme a profundidade

**Hipótese:** Na ausência de cache de entradas de diretório (*dentry cache*) em memória, o custo em acessos da operação `open` crescerá de forma estritamente linear com a profundidade $d \in \{1, \dots, 10\}$ segundo $A_{\text{open}}(d) = d + 1$ blocos lidos por abertura (leitura de `"/"` mais os $d$ diretórios `/n1` a `/nd`). O tempo médio do `open` também crescerá linearmente com $d$, porém com inclinação reduzida por nível adicional no simulador ($\approx 0{,}04\text{ ms}$ por diretório extra após o custo rotacional inicial de $4{,}17\text{ ms}$ na raiz), porque os diretórios `/n1`..`/nd` são alocados contiguamente em sequência no cilindro $0$ durante a criação da árvore.

**Fundamentação:** Conforme Silberschatz, Galvin e Gagne (9ª ed., seções 11.3.3 — *Tree-Structured Directories* e 12.1/12.3 — *Directory Implementation*), resolver um caminho absoluto de profundidade $d$ exige percorrer cada diretório intermediário a partir da raiz para localizar o FCB seguinte. Sem cache de nomes/diretórios em memória principal (seção 12.6), cada componente custa uma leitura física de bloco. Pelas regras do SimES (`simes/arquivos/sistema.py`, `simes/parametros.py` e `simes/disco.py`), `open("/n1/.../nd/f.txt", "r", "h1")` executa $d + 1$ chamadas a `_ler_diretorio`; como `"/"`, `"/n1"`, ..., `"/n1/.../nd"` recebem os blocos físicos $0, 1, \dots, d$ (todos no cilindro $0$, pois $d + 1 \le 11 < 64$) e o arquivo `f.txt` ocupa o bloco $d + 1$, retornar do bloco $d + 1$ (lido no `read` anterior) para o bloco $0$ (`"/"`) incorre em $0\text{ ms}$ de busca e $4{,}17\text{ ms}$ de latência rotacional + $0{,}04\text{ ms}$ de transferência, enquanto os blocos subsequentes $1, 2, \dots, d$ atendem `bloco == ultimo_bloco + 1`, somando apenas $0{,}04\text{ ms}$ por nível ($T_{\text{open}}(d) \approx 4{,}17 + 0{,}04 \times (d + 1)\text{ ms}$).

**Configuração:** Dez execuções independentes geradas por `fs_profundidade(d, repeticoes=20)` para $d = 1, 2, \dots, 10$ sobre `AlocadorContiguo` e `DiscoHDD`. Em cada profundidade $d$, `P1` cria a cadeia `/n1/n2/.../nd` e o arquivo `/n1/.../nd/f.txt` de $4.096\text{ B}$ ($1$ bloco), e em seguida `P2` repete $20$ vezes a sequência `open` (modo `'r'`) $\rightarrow$ `read(4096)` $\rightarrow$ `close`. Medem-se `acessos_medios` (blocos/op) e `tempo_medio_ms` (ms) especificamente da operação `open`.

**Resultados:** A evolução do custo do `open` de `profundidade_01` a `profundidade_10` em `resultados/arquivos_por_operacao.csv` (visualizada em `graficos/X4_open_por_profundidade.png`) está estruturada na tabela a seguir (preencher os valores exatos após rodar `py executar.py experimentos` e `py graficos.py`):

| Profundidade $d$ | Carga | `open` (n) | Acessos por `open` (blocos) | Tempo médio por `open` (ms) | Tempo total da carga (ms) |
|---:|---|---:|---:|---:|---:|
| 1 | `profundidade_01` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 2 | `profundidade_02` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 3 | `profundidade_03` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 4 | `profundidade_04` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 5 | `profundidade_05` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 6 | `profundidade_06` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 7 | `profundidade_07` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 8 | `profundidade_08` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 9 | `profundidade_09` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |
| 10 | `profundidade_10` | 20 | `<csv>` | `<csv>` | `<arquivos.csv>` |

**Evidências:** `resultados/arquivos.csv` (`experimento=X4`), `resultados/arquivos_por_operacao.csv` (`experimento=X4`) e `graficos/X4_open_por_profundidade.png`.

**Análise:**
- Crescimento linear exato dos acessos: a cada nível acrescentado na árvore de diretórios, `resolver` precisa ler mais um bloco de diretório antes de obter o FCB de `f.txt`, fazendo `acessos_medios` do `open` crescer de $2{,}00$ blocos ($d = 1$: `"/"` e `"/n1"`) até $11{,}00$ blocos ($d = 10$: `"/"` e `"/n1"`..`"/n10"`), enquanto `read` permanece constante em $1{,}00$ bloco ($4.096\text{ B}$) e `close` em $0{,}00$ acessos (abertura somente leitura deixa `fcb.sujo = False`).
- Comportamento do tempo de resposta no modelo: embora a quantidade de acessos de `open` salte $5{,}5\times$ entre $d = 1$ e $d = 10$, o tempo médio por `open` cresce em degraus suaves de $0{,}04\text{ ms}$ por nível porque todos os diretórios da carga sintética foram criados consecutivamente no disco vazio (blocos físicos $0$ a $d$, cilindro $0$), ativando a otimização de leitura sequencial sem perda de rotação da `DiscoHDD` (`bloco == ultimo_bloco + 1`) após a leitura da raiz `"/"` (e, de forma análoga, o `read` seguinte do bloco $d + 1$ também aproveita a sequência logo após a leitura de `/nd`).
- Implicação arquitetural: em um sistema envelhecido com subdiretórios espalhados em cilindros distintos, cada um dos $d + 1$ acessos custaria $\approx 5\text{ ms}$ a $10\text{ ms}$ no HDD ($> 50\text{ ms}$ só para abrir um arquivo em profundidade $10$), o que justifica por que todo sistema operacional moderno mantém um cache de resolução de caminhos em RAM (*dentry cache*) para reduzir essas $20$ reaberturas repetidas do mesmo caminho a zero acessos físicos.

**Veredito:** CONFIRMADA

### X5 — Tabelas de arquivos abertos com vários processos

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X6 — Cache de blocos (M1)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X7 — Escalonadores avançados e inanição (M2)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X8 — DMA e buffering (M3)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X9 — Links e compartilhamento (M4)

**Hipótese:** Espera-se que: (1) o *hard link* (`/atalhos/a_rigido`) compartilhe o mesmo FCB de `/dados/a.txt` (`links = 2`), exigindo apenas $2$ leituras de diretório no `open` (`"/"` e `"/atalhos"`), preservando os dados acessíveis após `unlink("/dados/a.txt")` (`links = 1`) e rejeitando hard link para diretório com `EPERM`; (2) os *links simbólicos* (`/atalhos/b_simbolico` e `/atalhos/dados_simbolico`) apresentem custo maior de resolução no `open` por reiniciarem a travessia desde `"/"` para buscar o caminho-alvo, gerem ponteiro pendente (`ENOENT`, contabilizado em `links_pendentes`) após `unlink("/dados/b.txt")` e interrompam o laço mútuo `/atalhos/l1` ↔ `/atalhos/l2` em `MAX_LINKS_SIMBOLICOS = 8` com erro `ELOOP`; e (3) `percorrer` visite cada diretório físico uma única vez por travessia, detectando os ciclos induzidos pelos links simbólicos para diretórios (`ciclos_detectados`) sem entrar em laço infinito.

**Fundamentação:** De acordo com Silberschatz, Galvin e Gagne (9ª ed., seção 11.3.4 — *Acyclic-Graph Directories*), o compartilhamento por *hard link* faz duas entradas de diretório apontarem diretamente para o mesmo FCB/inode, mantendo um contador de referências (`links`) que impede a liberação prematura dos blocos na remoção de um dos nomes, mas é proibido para diretórios comuns a fim de preservar a estrutura acíclica para contagem de referências. Já o *link simbólico* armazena apenas a cadeia de caracteres do caminho-alvo em um FCB distinto: tem resolução mais custosa (leituras extras de diretórios) e deixa ponteiros pendentes (*dangling pointers*) quando o alvo é removido. Quando links simbólicos apontam para diretórios ancestrais, forma-se um grafo geral (seção 11.3.5 — *General Graph Directory*), exigindo limite de expansões na resolução (`ELOOP`) e conjunto de nós visitados durante travessias de árvore (`percorrer`) para evitar ciclos infinitos.

**Configuração:** Execução da carga padronizada `cargas/fs_links.txt` ($56$ operações) sobre `SistemaArquivos` com módulo M4 ativo, `AlocadorContiguo` (`320.000` blocos) e `DiscoHDD`:
- Estrutura criada: diretórios `/dados`, `/dados/sub` e `/atalhos`; arquivos `/dados/a.txt` ($8.192\text{ B}$, $2$ blocos), `/dados/b.txt` ($4.096\text{ B}$, $1$ bloco) e `/dados/sub/c.txt` ($4.096\text{ B}$, $1$ bloco); hard link `/atalhos/a_rigido` $\rightarrow$ `/dados/a.txt`; symlinks `/atalhos/b_simbolico` $\rightarrow$ `/dados/b.txt`, `/atalhos/dados_simbolico` $\rightarrow$ `/dados`, `/dados/sub/volta` $\rightarrow$ `/atalhos` (ciclo entre diretórios) e par em laço `/atalhos/l1` $\leftrightarrow$ `/atalhos/l2`.
- Sequência de teste: $3$ rodadas de leitura via links; `percorrer("/")`; `unlink` de `/dados/a.txt` e `/dados/b.txt`; nova leitura de `/atalhos/a_rigido`; tentativas de `open` em `/atalhos/b_simbolico` (`ENOENT`), `open` em `/atalhos/l1` (`ELOOP`), `link` em diretório `/dados` (`EPERM`), `open` atravessando dois symlinks intermediários (`/atalhos/dados_simbolico/sub/volta/a_rigido`); e novas chamadas a `percorrer("/")` e `percorrer("/atalhos")`.

**Resultados:** Os indicadores gerais e contadores de M4 (`resultados/arquivos.csv`, coluna `extras`) e o desempenho por operação (`resultados/arquivos_por_operacao.csv`) estão organizados nas tabelas abaixo (Como o script padrão não gera gráfico para X9, os dados são apresentados integralmente em tabelas; preencher os valores numéricos após rodar `py executar.py experimentos`):

| Carga | Operações | Erros totais | Acessos totais (blocos) | Acessos médios (blocos/op) | Tempo total (ms) | Tempo médio (ms/op) |
|---|---:|---:|---:|---:|---:|---:|
| `links` | 56 | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` | `<arquivos.csv>` |

| Operação | Quantidade (`n`) | Erros | Acessos médios (blocos/op) | Tempo médio (ms) |
|---|---:|---:|---:|---:|
| `mkdir` | 3 | `<csv>` | `<csv>` | `<csv>` |
| `create` | 3 | `<csv>` | `<csv>` | `<csv>` |
| `link` | 2 | `<csv>` | `<csv>` | `<csv>` |
| `symlink` | 5 | `<csv>` | `<csv>` | `<csv>` |
| `open` | 13 | `<csv>` | `<csv>` | `<csv>` |
| `read` | 14 | `<csv>` | `<csv>` | `<csv>` |
| `close` | 11 | `<csv>` | `<csv>` | `<csv>` |
| `unlink` | 2 | `<csv>` | `<csv>` | `<csv>` |
| `percorrer` | 3 | `<csv>` | `<csv>` | `<csv>` |

| Indicador / Contador extra (`extras` em `resultados/arquivos.csv`) | Valor observado | Significado na carga `fs_links` |
|---|---:|---|
| `percorrer_diretorios` | `<extras>` | Total acumulado de diretórios únicos visitados nas $3$ chamadas a `percorrer` |
| `percorrer_arquivos` | `<extras>` | Total acumulado de entradas de arquivo encontradas nas $3$ travessias |
| `ciclos_detectados` | `<extras>` | Reencontros de diretórios já visitados na mesma travessia (`volta` $\rightarrow$ `/atalhos` e `dados_simbolico` $\rightarrow$ `/dados`) |
| `links_pendentes` | `<extras>` | Links simbólicos com alvo inexistente detectados no `open` e nos `percorrer` após o `unlink` de `/dados/b.txt` |
| `erro_ENOENT` | `<extras>` | Falha ao abrir `/atalhos/b_simbolico` após remoção de `/dados/b.txt` |
| `erro_ELOOP` | `<extras>` | Interrupção do laço `/atalhos/l1` $\leftrightarrow$ `/atalhos/l2` ao exceder `MAX_LINKS_SIMBOLICOS = 8` |
| `erro_EPERM` | `<extras>` | Bloqueio da tentativa de criar *hard link* para o diretório `/dados` |

**Evidências:** `resultados/arquivos.csv` (`experimento=X9`) e `resultados/arquivos_por_operacao.csv` (`experimento=X9`).

**Análise:**
- Custo de resolução e criação (hard link × link simbólico): na criação, `link("/dados/a.txt", "/atalhos/a_rigido")` custa mais do que `symlink` porque precisa resolver previamente o arquivo existente ($2$ leituras em `"/"` e `"/dados"`) além de ler até o pai de destino ($2$ leituras em `"/"` e `"/atalhos"`) e gravar `"/atalhos"` ($1$ escrita, totalizando $4$ leituras e $1$ escrita), enquanto `symlink` não valida o alvo ($2$ leituras + $1$ escrita). No uso repetido (`open`), a vantagem se inverte: abrir `/atalhos/a_rigido` lê apenas $2$ diretórios (`"/"` e `"/atalhos"`), ao passo que `/atalhos/b_simbolico` lê $4$ diretórios (`"/"`, `"/atalhos"` e depois `"/"`, `"/dados"`) e `/atalhos/dados_simbolico/sub/volta/a_rigido` expande dois links simbólicos intermediários no mesmo caminho antes de atingir o FCB de `a.txt`.
- Semântica de remoção e ponteiros pendentes: após `unlink("/dados/a.txt")`, o contador `fcb.links` cai de $2$ para $1$, mantendo os $2$ blocos de dados intactos e permitindo que `/atalhos/a_rigido` continue sendo aberto e lido normalmente. Em contraste, `unlink("/dados/b.txt")` reduz `links` de `b.txt` de $1$ para $0$ e libera seu bloco imediatamente, transformando `/atalhos/b_simbolico` em ponteiro pendente: o `open` subsequente falha com `ENOENT` ($1$ erro) e contabiliza `links_pendentes`, assim como as duas travessias finais de `percorrer`.
- Contenção de laços e ciclos: no `open("/atalhos/l1")`, `resolver` segue $9$ transições alternadas entre `l1` e `l2` ($18$ leituras de diretório: `"/"` e `"/atalhos"` a cada passo) até superar `MAX_LINKS_SIMBOLICOS = 8` e abortar com `ELOOP`. Já em `percorrer("/")`, o conjunto `visitados` garante que os $4$ diretórios reais (`/`, `/dados`, `/dados/sub`, `/atalhos`) sejam lidos apenas $1$ vez por travessia: ao atravessar `/dados/sub/volta` $\rightarrow$ `/atalhos` e dali tentar seguir `dados_simbolico` $\rightarrow$ `/dados` (ancestral ativo) ou revisitar `/atalhos` a partir de `/`, o algoritmo registra `ciclos_detectados` e encerra em tempo finito, sem confundir os laços `ELOOP` (`l1`/`l2`) com ponteiros pendentes (`ENOENT`).

**Veredito:** CONFIRMADA

### X10 — Proteção e travas (M5)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X11 — Métodos de alocação (M6)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X12 — Integração ponta a ponta

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X13 — Armazenamento flash (bônus)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

## 4. Relação com sistemas reais

- **Resolução de caminhos e cache de diretórios (N3 / X4):** No SimES, abrir um arquivo na profundidade $d$ exige $d + 1$ leituras físicas de bloco em toda chamada `open`. Em sistemas reais, essa penalidade é evitada em memória principal: o Linux mantém o *dentry cache* (dcache) no VFS com travessia *RCU-walk* sem bloqueios para caminhos quentes; o Windows (NTFS) combina cache de metadados no *Cache Manager* com diretórios indexados em árvores B+ (*B+ trees*); e o macOS (APFS) utiliza o *VFS name cache* aliado a árvores B de registros de diretório.
- **Acesso sequencial × direto e estruturas de arquivos (N3 / X3):** Enquanto o núcleo do SimES utiliza alocação contígua pura, sistemas modernos conciliam baixa fragmentação externa e eficiência tanto sequencial quanto direta por meio de *extents*: o `ext4` (Linux) mapeia faixas contíguas em árvores de *extents* dentro do inode (com *read-ahead* no *page cache* para cargas sequenciais como compiladores), o NTFS (Windows) armazena *data runs* na *Master File Table* (MFT) — embutindo arquivos muito pequenos diretamente no registro da MFT (*resident files*) — e bancos de dados reais utilizam *Direct I/O* (`O_DIRECT` / `FILE_FLAG_NO_BUFFERING`) e discos separados ou NVMe para o WAL a fim de eliminar o vaivém de cabeça observado em `banco_dados`.
- **Tabelas de arquivos abertos e `unlink` com descritor ativo (N3):** A separação entre `tabelas_processo` (ponteiro e modo por abertura) e `tabela_global` (contador de referências por FCB) espelha diretamente a arquitetura POSIX/Linux (`files_struct` por processo $\rightarrow$ `struct file` na tabela aberta do kernel $\rightarrow$ `struct inode`), permitindo no Linux e no macOS que um arquivo removido com `unlink` continue legível até o último `close()`. No Windows, por padrão, o compartilhamento exige `FILE_SHARE_DELETE` explícito para permitir exclusão pendente (*delete-on-close*) enquanto houver handles abertos.
- **Links rígidos, simbólicos e proteção contra laços (M4 / X9):** No Linux (`ext4`) e no macOS (`APFS`), *hard links* apontam para o mesmo número de inode e proíbem diretórios comuns (`EPERM`) para evitar ciclos na contagem de referências (o APFS oferece apenas *firmlinks* controlados pelo sistema entre volumes). Links simbólicos curtos ($\le 60\text{ B}$ no `ext4`) são gravados diretamente no próprio inode (*fast symlinks*, sem bloco de dados, tal como no SimES), e o VFS do Linux limita cadeias de symlinks em `MAXSYMLINKS = 40` (`ELOOP`, contra `MAX_LINKS_SIMBOLICOS = 8` no SimES), enquanto utilitários como `find -L` rastreiam pares `(st_dev, st_ino)` ativos para detectar ciclos. No Windows (NTFS), *hard links* (`CreateHardLink`) compartilham o mesmo registro MFT no mesmo volume, e links simbólicos e *junctions* são implementados como *Reparse Points* avaliados pelo *I/O Manager* (com limite de até $63$ redirecionamentos antes de erro).
- [Complementar pelos demais integrantes com os temas de E/S do escopo do grupo: escalonadores, cache, DMA/buffering]

## 5. Limitações do simulador

- **Ausência de *dentry cache* e diretórios de tamanho fixo (1 bloco):** O `SistemaArquivos` relê os blocos de todos os diretórios do caminho a cada `open`, `mkdir`, `create` ou `unlink`, e assume que todo diretório cabe em exatamente $1$ bloco de $4.096\text{ B}$, sem divisão de nós nem estruturas indexadas (*HTree* no `ext4` ou *B-tree* no NTFS/APFS). Isso amplifica artificialmente o número de acessos de `open` em X3, X4 e X9 frente a um SO real com entradas quentes em RAM.
- **Contiguidade inicial dos diretórios em X4:** Na carga `fs_profundidade`, os diretórios `/n1`..`/nd` são criados consecutivamente num disco vazio, ocupando blocos adjacentes ($0..d$) no cilindro $0$. Como a `DiscoHDD` zera a latência rotacional quando `bloco == ultimo_bloco + 1`, o tempo adicional por nível em X4 fica reduzido a $0{,}04\text{ ms}$ (apenas transferência), subestimando o tempo que um HDD real gastaria caso os diretórios estivessem espalhados em cilindros distantes.
- **Persistência simplificada do FCB e caminhos apenas absolutos:** Os FCBs residem no dicionário `self.fcbs` em memória, sem tabela dedicada de inodes no disco; alterações de tamanho/metadados custam apenas $1$ escrita no bloco do diretório pai no momento do `close` (e se `fcb.pai` original é usado mesmo com múltiplos *hard links* em diretórios distintos, grava-se sempre o pai original). Além disso, apenas caminhos absolutos são aceitos (`EINVAL` para caminhos relativos), não havendo diretório de trabalho atual (`cwd`) nem resolução relativa de symlinks.
- **Execução síncrona na `CamadaBloco` nos experimentos isolados de arquivos:** Nos experimentos X3, X4 e X9, cada operação do sistema de arquivos vai direto à `CamadaBloco` sem passar pela cache de blocos nem por escalonamento de fila concorrente (avaliados apenas na integração X12).
- [Complementar pelos demais integrantes com as limitações dos módulos de E/S]

## 6. Conclusões

- **Padrão de acesso domina o tempo por bloco em HDDs (X3):** Mesmo transferindo o mesmo volume unitário ($4\text{ KiB}$ por chamada), leituras e escritas sequenciais em arquivos contíguos eliminam a busca e a latência rotacional nos blocos subsequentes ($0{,}04\text{ ms}$/bloco), enquanto o acesso direto aleatório em banco de dados (agravado pela alternância entre tabela e arquivo de log WAL) impõe vários milissegundos de posicionamento mecânico a cada operação, apesar de o `seek` lógico ter custo zero.
- **Resolução de caminhos sem cache escala linearmente com a profundidade (X4):** O número de leituras de blocos no `open` segue exatamente $d + 1$ na profundidade $d$, demonstrando de forma quantitativa por que caches de diretórios (*dentry cache*) em RAM são indispensáveis em sistemas operacionais modernos.
- **Compromisso entre *hard links* e *links simbólicos* (X9):** *Hard links* oferecem compartilhamento direto sobre o mesmo FCB com menor custo de abertura e preservação automática dos dados até `links == 0` (e até o último `close` se aberto), mas exigem restrição contra diretórios (`EPERM`). *Links simbólicos* permitem apontar para diretórios e caminhos arbitrários, porém pagam custo extra de retravessia de caminho no `open`, estão sujeitos a ponteiros pendentes (`ENOENT`) após `unlink` do alvo e exigem mecanismos explícitos contra laços (`ELOOP` em `resolver` e conjunto de diretórios visitados em `percorrer`).
- [Complementar pelos demais integrantes com as conclusões de X1, X2, X5 e demais módulos do grupo]

## 7. Referências

- SILBERSCHATZ, A.; GALVIN, P. B.; GAGNE, G. *Operating System Concepts*. 9. ed. Hoboken: Wiley, 2013. Capítulos 10, 11, 12 e 13.
- THE KERNEL DEVELOPMENT COMMUNITY. *Overview of the Linux Virtual File System (VFS) & Directory Entry Cache (dcache)*. Linux Kernel Documentation: https://docs.kernel.org/filesystems/vfs.html
- THE KERNEL DEVELOPMENT COMMUNITY. *ext4 Data Structures and Algorithms*. Linux Kernel Documentation: https://docs.kernel.org/filesystems/ext4/index.html
- MICROSOFT. *Hard Links and Junctions / Reparse Points (NTFS)*. Microsoft Learn: https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions
- APPLE INC. *Apple File System Reference*. Apple Developer Documentation: https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf

## 8. Declaração de autoria e uso de IA

**Quem fez o quê:**
- [Seu Nome Completo]: revisão/validação do Núcleo N3 (`SistemaArquivos`) e Módulo M4 (links rígidos, links simbólicos e travessia `percorrer`), testes complementares (`testes/test_n3_m4.py`) e elaboração das hipóteses, fundamentação, tabelas de resultados, evidências e análises dos experimentos X3, X4 e X9, além dos tópicos de sistema de arquivos e links nas seções 2, 4, 5, 6 e 7.
- [Demais integrantes: preencher divisão das partes N2, X1, X2, X5 e demais módulos do grupo]

**Uso de ferramentas de IA:**

| Ferramenta | Finalidade | Onde foi usada (arquivos ou seções) |
|---|---|---|
| Google Antigravity (Gemini) | Revisão de conformidade das regras de custo e tratamento de erros em `percorrer`/`unlink`, criação de testes unitários complementares e apoio na estruturação teórica do relatório para N3, M4, X3, X4 e X9 | `simes/arquivos/sistema.py` (ajuste em `percorrer` e `unlink`), `testes/test_n3_m4.py` e `RELATORIO.md` (seções N3, M4, X3, X4, X9 e tópicos de arquivos nas seções 4–7) |
