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

### X8 — DMA e buffering (M3)

**Hipótese:** [ ]

**Fundamentação:** [ ]

**Configuração:** [ ]

**Resultados:** [ ]

**Evidências:** [ ]

**Análise:** [ ]

**Veredito:** [ ]

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
