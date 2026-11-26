# Relatório — SimES: simulador de E/S e de sistema de arquivos

**Integrantes:** Gabriel Ribeiro Kowaleski, Jully Anne Seyffert da Silva Jara, Maria Rita Rodrigues, Mayra Bordin de Abreu

**Repositório:** https://github.com/MRita011/T2-SISOP

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
| N2 · Subsistema de E/S (SSTF, SCAN, polling, interrupção) | completo | Implementação concluída e testes aprovados. |
| N3 · Sistema de arquivos | completo | Implementação concluída e testes aprovados. |
| N4 · Experimentos X1–X5 e relatório | [completo / parcial] | [ ] |
| M1 · Cache de blocos | completo | Implementação concluída e testes aprovados. |
| M3 · DMA e buffering | completo | Implementação concluída e testes aprovados. |
| M4 · Links e compartilhamento | completo | Implementação concluída e testes aprovados. |
| Integração (grupos de 4) | completo | Implementação concluída, teste aprovado e experimento X12 executado, analisado e com evidências geradas. |
| [Bônus flash] | [completo / parcial / não feito] | [ ] |

Resultado dos testes automáticos (`python3 executar.py testes`): Ran 26 tests in 0.008s — OK (skipped=4)

Os quatro testes ignorados correspondem a M2, M5 e M6, que não fazem parte dos módulos escolhidos pelo grupo.

## 2. Implementação

### N2 — Subsistema de E/S

**Onde:** `simes/es/escalonadores.py`, nos escalonadores SSTF e SCAN, e `simes/es/cpu.py`, no cálculo dos custos de polling e interrupção.

**Decisões:** No SSTF, a escolha da próxima requisição foi feita considerando a menor distância em relação à posição atual do braço do disco. No SCAN, foi mantida a direção do movimento enquanto existiam requisições naquele sentido e, quando necessário, a direção era invertida. Para polling e interrupção, foram seguidas as regras de custo já definidas pelo simulador, mantendo cada forma de tratamento de E/S separada para permitir a comparação nos experimentos.

**Dificuldades:** O principal cuidado nessa parte foi manter corretamente a posição e a direção do braço durante o escalonamento, principalmente no SCAN. Também foi necessário seguir exatamente as fórmulas de custo previstas pelo simulador para que polling e interrupção apresentassem os resultados esperados nos testes.

### N3 — Sistema de arquivos

**Onde:** `simes/arquivos/sistema.py`, principalmente nas funções de resolução de caminhos e nas operações `mkdir`, `create`, `open`, `read`, `write`, `seek`, `close` e `unlink`, além das tabelas de arquivos abertos.

**Decisões:** A resolução dos caminhos foi feita percorrendo os diretórios até localizar o arquivo ou diretório solicitado. Para os arquivos abertos, foram utilizadas uma tabela global, compartilhada entre os processos, e tabelas individuais por processo, onde cada abertura mantém sua própria posição e modo de acesso. As operações de leitura e escrita atualizam essa posição, enquanto o `seek` permite alterá-la diretamente. Também foi mantida a regra de que um arquivo removido com `unlink` não tem seus blocos liberados enquanto ainda existir algum processo com ele aberto.

**Dificuldades:** Essa foi uma das partes que exigiu mais atenção por causa da relação entre as várias operações. Além de fazer cada função funcionar individualmente, foi necessário manter corretamente as tabelas de arquivos abertos, a posição de cada handle e as regras de custo de acesso ao disco. O caso do `unlink` com um arquivo ainda aberto também exigiu cuidado para que os blocos só fossem liberados no último `close`.

### M1 — Cache de blocos

**Onde:** `simes/es/cache.py`.

**Decisões:** Foram implementadas as políticas LRU e FIFO para substituição dos blocos da cache, além das políticas de escrita `write-through` e `write-back`. A ideia foi manter separadas as decisões de qual bloco deve sair da cache e de quando uma escrita precisa chegar ao dispositivo. Também foi considerado o comportamento dos blocos modificados em situações de sincronização e queda de energia, conforme as regras previstas para o módulo.

**Dificuldades:** O principal cuidado foi diferenciar corretamente o comportamento de LRU e FIFO, já que no LRU o uso recente de um bloco interfere na ordem de substituição, enquanto no FIFO importa a ordem em que ele entrou na cache. Outro ponto importante foi manter clara a diferença entre `write-through` e `write-back`, principalmente em relação aos blocos que ainda estavam modificados na cache.

### M3 — DMA e buffering

**Onde:** `simes/es/cpu.py`, na parte referente ao DMA, e `simes/es/buffering.py`, na simulação dos buffers.

**Decisões:** Para o DMA, foi considerado que a CPU participa principalmente da configuração da transferência e do tratamento da interrupção ao final, reduzindo sua participação durante a transferência dos blocos. No buffering, foi simulada a relação entre produtor e dispositivo utilizando diferentes quantidades de buffers, acompanhando o momento em que cada bloco é produzido, consumido e quando um buffer volta a ficar disponível.

**Dificuldades:** No DMA, o principal cuidado foi representar corretamente a diferença de custo para a CPU em relação ao polling e à interrupção. Já no buffering, foi necessário controlar a ordem dos eventos para evitar que o produtor reutilizasse um buffer antes de ele estar realmente livre. Também foi preciso calcular corretamente o tempo em que o produtor ficou bloqueado e a utilização do dispositivo.

### M4 — Links e compartilhamento

**Onde:** `simes/arquivos/sistema.py`, nas operações relacionadas a hard links, links simbólicos e travessia da árvore de diretórios.

**Decisões:** Nos hard links, diferentes nomes podem apontar para o mesmo arquivo, mantendo a contagem de links associada ao FCB. Nos links simbólicos, foi criado um objeto próprio que guarda o caminho do alvo, permitindo inclusive que esse alvo ainda não exista. A travessia também considera links simbólicos para diretórios e registra situações de links pendentes e ciclos, evitando continuar indefinidamente quando um diretório já visitado é encontrado novamente.

**Dificuldades:** A parte mais delicada foi tratar os links simbólicos sem criar uma resolução infinita. Foi necessário diferenciar hard links de links simbólicos, identificar links cujo alvo não existe e controlar os diretórios já visitados durante a travessia para detectar ciclos sem continuar entrando no mesmo caminho.

### Integração ponta a ponta

**Onde:** `simes/integracao.py`, função `historico_para_requisicoes`.

**Decisões:** A integração foi implementada convertendo o histórico de acessos ao disco gerado pela camada de blocos em objetos `Requisicao` utilizados pelo subsistema de E/S. Os registros são organizados pelo instante de chegada e cada acesso recebe um identificador sequencial a partir de zero. Foram mantidas as informações de processo, tipo de operação, bloco acessado e quantidade de blocos. Nos casos em que mais de um acesso possui o mesmo instante de chegada, a ordem existente no histórico é preservada. A partir dessa conversão, as requisições podem passar pela cache e pelos escalonadores de disco no experimento X12.

**Dificuldades:** O principal cuidado foi garantir que a conversão do histórico para as requisições de E/S preservasse corretamente a ordem de chegada e as informações de cada acesso, permitindo que a saída do sistema de arquivos fosse utilizada diretamente pelas camadas seguintes do simulador.

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

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X4 — Custo de resolver caminhos conforme a profundidade

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X5 — Tabelas de arquivos abertos com vários processos

**Hipótese:** A tabela global terá uma entrada por arquivo distinto aberto (no máximo as 12 páginas), enquanto cada processo terá no máximo 3 entradas (3 handles por trabalhador). A soma das tabelas por processo (8 × 3 = 24 aberturas) será maior que a tabela global, porque o sorteio de 3 entre 12 páginas faz vários processos abrirem a mesma página, e o contador de aberturas passará de 1. Esperamos ainda que o `open` custe 2 leituras (diretórios `/` e `/www`) e que o `close` não grave nada, pois a carga só lê.

**Fundamentação:** Silberschatz, seção 11.1.2: o SO mantém uma tabela de arquivos abertos por processo (posição, modo) e uma tabela global (cópia do FCB e contador de aberturas), cuja entrada é removida quando o contador zera. As regras de custo do `sistema.py` definem `open` = leitura dos diretórios do caminho, `read` = leitura dos blocos cobertos e `close` = escrita do diretório pai somente se o FCB estiver sujo.

**Configuração:** Carga `fs_servidor_web` (semente 2026): P0 cria `/www` e 12 páginas de 8 a 96 KiB; 8 trabalhadores (P1–P8) fazem 40 rodadas, e em cada uma abrem 3 páginas sorteadas, leem inteiras em blocos de 16 KiB e fecham. Alocação contígua, bloqueio consultivo, 6.279 operações, sem erros. Gerado por `python3 executar.py experimentos` (função `x5`).

**Resultados:**

| Indicador | Valor |
|---|---|
| Máximo da tabela global | 12 entradas |
| Máximo da tabela por processo | 3 entradas |
| Máximo da soma das tabelas por processo | 24 entradas |
| Máximo do contador de aberturas | 6 |
| Acessos ao disco (total) | 17.824 (2,84 por operação) |
| Tempo total | 9.354,08 ms (1,49 ms por operação) |

| Operação | Quantidade | Acessos médios | Tempo médio (ms) |
|---|---|---|---|
| open | 960 | 2,00 | 4,27 |
| read | 4.346 | 3,65 | 1,18 |
| close | 960 | 0,00 | 0,00 |

**Evidências:**
- `resultados/arquivos.csv` (linha X5)
- `resultados/arquivos_por_operacao.csv` (linhas X5)
- `graficos/X5_tabelas.png`

![X5 — tabelas de arquivos abertos](graficos/X5_tabelas.png)

**Análise:** A tabela global guarda uma entrada por arquivo aberto, com um contador que soma as aberturas de todos os processos. A tabela por processo guarda uma entrada por abertura, com posição e modo, o que permite a cada processo ler no seu próprio ritmo. Com 24 aberturas simultâneas (8 × 3), a global chegou a no máximo 12 entradas, metade da soma das tabelas por processo (24): o compartilhamento evita duplicar o FCB de cada arquivo. O contador máximo de 6 mostra que, em algum momento, seis dos oito processos tinham a mesma página aberta. O `open` custa 2 acessos (diretórios `/` e `/www`, como manda a regra de custo) e 4,27 ms; esse valor é compatível com apenas um dos dois acessos pagar a latência rotacional de 4,17 ms, supondo que os blocos dos diretórios estão adjacentes. O `close` custa 0 porque a carga só lê e o FCB nunca fica sujo. No `read` (1,18 ms), as leituras seguintes de um mesmo arquivo são sequenciais e não pagam rotação; só a primeira leitura de cada abertura (cerca de 22% das leituras, 960 de 4.346) paga os 4,17 ms, o que é compatível com a média observada.

Relação com sistemas reais: no Linux, cada processo tem uma tabela de descritores que aponta para uma `struct file` (com a posição) e esta para o inode compartilhado, uma estrutura em três níveis; no Windows, cada processo tem uma tabela de handles que aponta para objetos de arquivo. Em ambos o desempenho de abrir arquivos depende também do cache de diretórios (dentry cache no Linux).

Limitações: o X5 roda sem cache de blocos, então todo `open` relê `/` e `/www` do disco (1.920 leituras de diretório), o que um SO real evitaria com o cache de diretórios. A carga é uma sequência simulada, sem concorrência real, e não há custo de travas nem limite de tamanho das tabelas.

**Veredito:** CONFIRMADA

### X6 — Cache de blocos (M1)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X8 — DMA e buffering

**Hipótese:** (a) O custo de CPU do DMA será constante e pequeno por requisição, independente do número de blocos, pois a CPU apenas programa a controladora e trata uma interrupção; a interrupção crescerá linearmente com o número de blocos (cópia de cada bloco pela CPU) e o polling ocupará a CPU durante todo o atendimento, sendo o mais caro. Com 1 bloco a interrupção será levemente mais barata que o DMA, e a partir de 2 blocos o DMA vence. O tempo de resposta será igual nos três modos, porque o modelo não acopla a CPU ao tempo do disco. (b) Com 1 buffer, produção e gravação se serializam; com 2 buffers elas se sobrepõem e o dispositivo (se for mais lento) vira o gargalo; um terceiro buffer trará ganho desprezível, pois os tempos são constantes.

**Fundamentação:** Silberschatz, seção 13.2.3 (DMA: a CPU programa a controladora e é avisada por uma única interrupção ao fim da transferência, em vez de uma por byte) e seção 13.4.2 (buffering: desacopla a velocidade do produtor da do dispositivo; o buffer duplo permite encher um buffer enquanto o outro é esvaziado). Custos do modelo (`parametros.py`): interrupção 0,015 ms, cópia 0,002 ms por bloco, programar o DMA 0,003 ms. Logo: DMA = 0,003 + 0,015 = 0,018 ms por requisição; interrupção = 0,015 + 0,002 × n ms por requisição.

**Configuração:** (1) CPU: carga aleatória em disco rígido, 1.000 requisições a cada 40 ms, FCFS, com 1, 8, 64 e 256 blocos por requisição, nos modos polling, interrupção e DMA. (2) Buffering: 500 blocos, produção de 2 ms, com 1, 2 e 3 buffers e consumo (gravação) de 0,5, 2 e 8 ms. Gerado por `python3 executar.py experimentos` (função `x8`).

**Resultados:**

CPU gasta com E/S (% do tempo total):

| Blocos por requisição | Polling | Interrupção | DMA |
|---|---|---|---|
| 1 | 25,17 | 0,0423 | 0,0448 |
| 8 | 25,87 | 0,3383 | 0,0448 |
| 64 | 31,44 | 2,7059 | 0,0448 |
| 256 | 50,52 | 10,8204 | 0,0448 |

Resposta média (ms), igual nos três modos: 12,30 (1 bloco), 12,71 (8), 16,16 (64) e 31,87 (256).

Buffering (500 blocos, produção de 2 ms):

| Consumo (ms) | Buffers | Tempo total (ms) | Bloqueio do produtor (ms) | Utilização do dispositivo (%) |
|---|---|---|---|---|
| 0,5 | 1 | 1.250,0 | 249,5 | 20,00 |
| 0,5 | 2 | 1.000,5 | 0,0 | 24,99 |
| 0,5 | 3 | 1.000,5 | 0,0 | 24,99 |
| 2,0 | 1 | 2.000,0 | 998,0 | 50,00 |
| 2,0 | 2 | 1.002,0 | 0,0 | 99,80 |
| 2,0 | 3 | 1.002,0 | 0,0 | 99,80 |
| 8,0 | 1 | 5.000,0 | 3.992,0 | 80,00 |
| 8,0 | 2 | 4.002,0 | 2.988,0 | 99,95 |
| 8,0 | 3 | 4.002,0 | 2.980,0 | 99,95 |

**Evidências:**
- `resultados/es.csv` (linhas X8)
- `resultados/buffering.csv`
- `graficos/X8_cpu.png`
- `graficos/X8_buffering.png`

![X8 — CPU gasta com E/S](graficos/X8_cpu.png)

![X8 — buffering](graficos/X8_buffering.png)

**Análise:** O custo do DMA ficou fixo em 0,0448% da CPU, o que equivale a 0,018 ms por requisição (1.000 × 0,018 ms ÷ cerca de 40.200 ms), qualquer que seja o tamanho da requisição. A interrupção cresce com o número de blocos porque a CPU copia cada um: de 0,0423% (1 bloco) a 10,82% (256 blocos), ou seja, cerca de 241 vezes o custo do DMA no maior tamanho. Com 1 bloco, a interrupção (0,017 ms) é um pouco mais barata que o DMA (0,018 ms); a partir de 2 blocos o DMA vence, como previsto. O polling gasta CPU durante todo o atendimento e por isso acompanha a ocupação do disco (cerca de 25% com 1 bloco, pois o atendimento leva cerca de 10 ms a cada 40 ms), chegando a 50,5% com 256 blocos. No gráfico `X8_cpu.png` o eixo vertical está em escala logarítmica, então a distância visual entre as barras subestima a diferença real. A resposta média é idêntica nos três modos, e isso é uma limitação do modelo: a CPU liberada pelo DMA não vira desempenho porque não há outro processo disputando a CPU.

No buffering, com 1 buffer o produtor só começa o próximo bloco depois que o dispositivo termina o anterior, então tempo = blocos × (produção + consumo) = 500 × 10 = 5.000 ms (com consumo de 8 ms). Com 2 buffers, produção e gravação se sobrepõem: o tempo cai para 2 + 500 × 8 = 4.002 ms e o dispositivo satura (99,95%), passando a ser o gargalo; o produtor fica bloqueado 6 ms por bloco (8 − 2) em regime permanente (498 × 6 = 2.988 ms). Quando o dispositivo é mais rápido que o produtor (consumo de 0,5 ms), o bloqueio some com 2 buffers e quem limita é o produtor (utilização de apenas 24,99%). No gráfico `X8_buffering.png`, as curvas de 2 e 3 buffers coincidem: o terceiro buffer praticamente não altera o resultado (diferença de 8 ms no bloqueio, só no transitório inicial). Como produção e consumo têm tempo constante, dois buffers já absorvem tudo, e o buffer circular só compensaria variações de ritmo.

Relação com sistemas reais: controladoras SATA (AHCI) e NVMe usam DMA com listas de descritores, e o driver recebe uma interrupção por comando concluído; o Linux também permite polling em dispositivos muito rápidos, onde o custo da interrupção passa a pesar. Buffers circulares aparecem em áudio e captura de vídeo, com filas de 3 ou mais buffers para absorver variações de tempo.

Limitações: o DMA modelado não tem disputa de barramento (roubo de ciclos), custo de IOMMU nem coerência de cache; os tempos de produção e gravação são constantes, sem variação, e há um único produtor e um único dispositivo. A resposta é igual nos três modos por não haver processos competindo pela CPU.

**Veredito:** CONFIRMADA

### X9 — Links e compartilhamento (M4)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

### X12 — Integração ponta a ponta

**Hipótese:** acredito que o uso da cache LRU diminua a quantidade de acessos físicos ao disco e ajude a melhorar o tempo de resposta, principalmente quando a carga reutiliza os mesmos blocos com mais frequência. Também é esperado que os escalonadores SSTF e SCAN reduzam o deslocamento do braço do disco em comparação com o FCFS, já que eles organizam o atendimento das requisições levando em conta a posição dos cilindros. Além disso, é provável que os resultados das cargas `compilador` e `banco_dados` sejam diferentes, porque cada uma possui um padrão de acesso aos arquivos.

**Fundamentação:** A hipótese foi construída a partir do funcionamento da cache e dos algoritmos de escalonamento de disco apresentados por Silberschatz, Galvin e Gagne. A ideia principal é que a cache pode evitar novos acessos físicos ao disco quando um bloco já utilizado continua disponível em memória, o que tende a trazer mais benefício em cargas que reutilizam os mesmos dados com frequência. Já os algoritmos de escalonamento definem a ordem em que as requisições de E/S serão atendidas. No FCFS, essa ordem segue a chegada das requisições, enquanto o SSTF prioriza as que estão mais próximas da posição atual do braço do disco e o SCAN percorre os cilindros em uma direção antes de inverter o movimento. Por isso, era esperado que a combinação entre cache e escalonamento tivesse impacto tanto no tempo de resposta quanto no deslocamento do braço do disco. Para essa fundamentação, foram consideradas principalmente as seções 10.4, 12.6 e 13.4.3 de Silberschatz, Galvin e Gagne (2013).

**Configuração:** No experimento foram utilizadas as cargas `compilador` e `banco_dados`. Primeiro, elas foram executadas pelo sistema de arquivos com alocação contígua e com o histórico de acessos ao disco sendo registrado. Depois, esse histórico foi transformado em requisições de E/S e passado pelos escalonadores FCFS, SSTF e SCAN. Cada um deles foi testado em duas situações: sem cache e com cache LRU de capacidade 1024, usando a política `write-back`. O dispositivo considerado foi um HDD e o tratamento de E/S foi feito por interrupção. No total, o experimento realizou 12 execuções.

**Resultados:**

| Carga | Escalonador | Cache | Resposta média (ms) | P95 (ms) | Deslocamento total | Acerto da cache |
|---|---|---|---:|---:|---:|---:|
| compilador+contigua | FCFS | nenhuma | 4970.8641 | 9510.3560 | 6900 | — |
| compilador+contigua | FCFS | LRU | 0.2259 | 0.0400 | 104 | 90.3985% |
| compilador+contigua | SSTF | nenhuma | 5170.1309 | 9032.7210 | 10 | — |
| compilador+contigua | SSTF | LRU | 0.1518 | 0.0400 | 80 | 90.4218% |
| compilador+contigua | SCAN | nenhuma | 5170.1309 | 9032.7210 | 10 | — |
| compilador+contigua | SCAN | LRU | 0.9446 | 0.0400 | 49996 | 90.3752% |
| banco_dados+contigua | FCFS | nenhuma | 6158.7547 | 11721.3590 | 360570 | — |
| banco_dados+contigua | FCFS | LRU | 2151.2855 | 7028.4870 | 260926 | 4.9296% |
| banco_dados+contigua | SSTF | nenhuma | 4106.2417 | 9494.9250 | 1518 | — |
| banco_dados+contigua | SSTF | LRU | 1411.9203 | 5915.0710 | 2697 | 4.8467% |
| banco_dados+contigua | SCAN | nenhuma | 4055.0737 | 10431.8940 | 19996 | — |
| banco_dados+contigua | SCAN | LRU | 1382.3897 | 5769.0160 | 40249 | 5.0953% |

Na carga `compilador`, a cache LRU teve um desempenho bem alto, com aproximadamente 90,4% de acertos nos três escalonadores. Com isso, o tempo médio de resposta caiu mais de 99,9% nas três configurações. Já na carga `banco_dados`, a taxa de acerto da cache ficou próxima de 5%, mas, mesmo assim, o tempo médio de resposta também apresentou uma redução considerável: aproximadamente 65,1% no FCFS, 65,6% no SSTF e 65,9% no SCAN.

**Evidências:** `resultados/es.csv` (experimento=X12); `graficos/X12_resposta.png`.

**Análise:** Os resultados mostram que o ganho obtido com a cache varia bastante de acordo com o padrão de acesso de cada carga. No caso de `compilador`, a taxa de acerto ficou em torno de 90,4%, o que indica que muitos dos blocos acessados voltaram a ser utilizados enquanto ainda estavam disponíveis na cache. Isso aparece de forma bem clara no tempo médio de resposta, que saiu de valores próximos de 5 segundos sem cache para menos de 1 ms nas três configurações com LRU.

Na carga `banco_dados`, o comportamento foi diferente. A taxa de acerto ficou próxima de 5%, mostrando que houve bem menos reutilização dos mesmos blocos. Mesmo assim, o uso da cache ainda reduziu o tempo médio de resposta em aproximadamente 65%. Essa diferença entre `compilador` e `banco_dados` reforça a ideia de que o benefício da cache depende diretamente do padrão de acesso da carga.

Em relação aos escalonadores, quando a cache não estava sendo utilizada, SSTF e SCAN apresentaram uma redução bem grande no deslocamento do braço do disco em comparação com o FCFS. Na carga `compilador`, por exemplo, o deslocamento foi de 6900 no FCFS e caiu para 10 tanto no SSTF quanto no SCAN. Em `banco_dados`, o FCFS chegou a 360570, enquanto o SSTF ficou em 1518 e o SCAN em 19996.

Por outro lado, esse comportamento não se repetiu da mesma forma em todas as configurações com cache. Em `compilador + LRU`, por exemplo, o SCAN apresentou deslocamento total de 49996, enquanto o FCFS ficou em 104 e o SSTF em 80. Isso mostra que, quando a cache reduz a quantidade de requisições que realmente chegam ao disco, o comportamento do escalonamento também pode mudar. No modelo do simulador, o SCAN continua seguindo uma direção de movimentação antes de inverter, o que pode gerar um deslocamento maior mesmo quando restam poucas requisições físicas para serem atendidas.

No geral, a integração mostrou que as camadas do sistema não funcionam de forma isolada. O padrão de acesso gerado pelo sistema de arquivos influencia o funcionamento da cache e, depois disso, também altera o conjunto de requisições que chega ao escalonador. Por isso, o desempenho final acaba sendo resultado da interação entre essas diferentes camadas.

**Veredito:** PARCIALMENTE CONFIRMADA

## 4. Relação com sistemas reais

Os resultados da integração ajudam a entender por que sistemas operacionais reais utilizam mecanismos de cache e diferentes formas de organizar as operações de E/S. Quando dados acessados recentemente continuam disponíveis em memória, alguns acessos ao armazenamento podem ser evitados, principalmente em situações em que os mesmos blocos são reutilizados com frequência. Em sistemas como Windows, Linux e macOS, esse processo envolve mecanismos bem mais complexos do que os representados pelo SimES. Mesmo assim, o X12 permite observar de forma simplificada uma ideia importante: uma decisão tomada em uma camada, como o uso da cache, pode alterar tanto a quantidade quanto o padrão das requisições que chegam posteriormente ao dispositivo de armazenamento.

## 5. Limitações do simulador

No X12, o SimES representa de forma simplificada a relação entre sistema de arquivos, cache, escalonamento e dispositivo. O experimento utiliza parâmetros fixos para o HDD e uma cache LRU com capacidade definida, o que não representa toda a complexidade encontrada em sistemas reais. Além disso, o simulador não considera vários fatores que poderiam interferir no desempenho, como diferentes níveis de cache, maior concorrência entre processos, otimizações feitas pelo hardware, características específicas dos controladores de armazenamento e mudanças dinâmicas nas políticas adotadas pelo sistema operacional. Por isso, os resultados são mais úteis para comparar o comportamento das políticas dentro do próprio simulador do que para prever exatamente o desempenho de uma máquina real.

## 6. Conclusões

- A integração ponta a ponta mostrou que as diferentes camadas do sistema influenciam umas às outras. O padrão de acesso gerado pelo sistema de arquivos interfere no funcionamento da cache e também modifica as requisições que chegam posteriormente ao escalonador.

- A cache LRU apresentou resultados bem diferentes entre as duas cargas. Em `compilador`, a taxa de acerto ficou em torno de 90,4%, enquanto em `banco_dados` ficou próxima de 5%, mostrando como o padrão de reutilização dos blocos interfere diretamente no benefício obtido com a cache.

- O comportamento dos escalonadores também variou conforme a carga e o uso da cache. Um exemplo foi a configuração `compilador + LRU`, em que o SCAN apresentou deslocamento total de 49996, enquanto o FCFS ficou em 104 e o SSTF em 80. Isso mostra que um algoritmo que apresenta vantagem em uma situação não necessariamente terá o mesmo comportamento quando as características das requisições mudam.

## 7. Referências

- SILBERSCHATZ, A.; GALVIN, P. B.; GAGNE, G. *Operating System Concepts*. 9. ed. Wiley, 2013.

## 8. Declaração de autoria e uso de IA

**Quem fez o quê:** Maria Rita Rodrigues: atuou no N2, com a implementação de SSTF, SCAN, polling e interrupção, e no N3, envolvendo resolução de caminhos, tabelas de arquivos abertos e operações de leitura, escrita, seek, close e unlink. Também trabalhou nos módulos M1, com cache LRU/FIFO e políticas write-through e write-back; M3, com DMA e buffering; e M4, com hard links, links simbólicos, links pendentes e detecção de ciclos. Por fim, ficou responsável pela integração ponta a ponta em `simes/integracao.py`, pela execução e análise do experimento X12 e pela discussão dos resultados e das limitações observadas.

**Uso de ferramentas de IA:**

| Ferramenta | Finalidade | Onde foi usada (arquivos ou seções) |
|---|---|---|
| Gemini | Apoio técnico na interpretação do enunciado, desenvolvimento e revisão. | `simes/integracao.py` e experimento X12. |
