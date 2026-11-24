# -*- coding: utf-8 -*-
"""
Módulo M3 (parte 2) — buffering entre um produtor e um dispositivo.

Referência: Silberschatz, 9ª ed., 13.4.2 (Buffering).

Cenário: um programa (produtor) gera `blocos` blocos de dados (ex.: uma câmera gravando
vídeo). Os dados vão para um dispositivo que grava um bloco em `consumo_ms`. Há `n_buffers`
buffers de UM bloco cada, e o produtor gera cada bloco DIRETAMENTE dentro de um buffer.

REGRAS DO MODELO (numere os blocos k = 1, 2, ..., blocos):
- para começar a gerar o bloco k, o produtor precisa (a) ter terminado o bloco k-1 e
  (b) ter um buffer livre. O buffer usado pelo bloco k é o liberado pelo bloco k - n_buffers
  (nos primeiros n_buffers blocos, todos os buffers estão livres no instante 0);
- gerar um bloco leva producao_ms; o tempo em que o produtor fica parado esperando por um
  buffer livre soma em bloqueio_produtor_ms;
- o dispositivo grava os blocos na ordem: começa o bloco k quando ele está pronto e quando
  terminou o bloco k-1; cada gravação leva consumo_ms; o buffer só fica livre quando a
  gravação termina;
- tempo_total_ms = instante em que o dispositivo termina de gravar o último bloco;
- utilizacao_dispositivo_pct = 100 * (blocos * consumo_ms) / tempo_total_ms.

Comparem n_buffers = 1 (buffer simples), 2 (duplo) e 3 (circular).
"""
def simular_buffering(n_buffers, producao_ms, consumo_ms, blocos):
    """Devolve dict com tempo_total_ms, bloqueio_produtor_ms e utilizacao_dispositivo_pct."""

    # não faz sentido ter 0 ou menos buffers
    if n_buffers <= 0:
        raise ValueError("n_buffers precisa ser > 0")

    # se não tem bloco pra processar, não tem tempo nem uso do dispositivo
    if blocos <= 0:
        return {
            "tempo_total_ms": 0,
            "bloqueio_produtor_ms": 0,
            "utilizacao_dispositivo_pct": 0.0,
        }

    fim_producao = [0.0] * blocos  # cada bloco que termina de ser produzido
    fim_consumo = [0.0] * blocos  # e aqui cada bloco que termina de ser consumido
    bloqueio_produtor_ms = 0.0  # tempo que o produtor ficou bloqueado esperando por um buffer livre

    fim_produtor_anterior = 0.0  # controla quando o produtor terminou o bloco anterior
    fim_dispositivo_anterior = 0.0  # controla quando o dispositivo terminou o bloco anterior

    for i in range(blocos):
        # o produtor precisa esperar o bloco anterior terminar de ser produzido
        instante_disponivel = fim_produtor_anterior

        # depois que todos os buffers já foram usados de uma vez,
        # o produtor precisa esperar o buffer usado pelo bloco i - n_buffers ficar livre
        if i >= n_buffers:
            instante_buffer_livre = fim_consumo[i - n_buffers]

            # se o buffer ainda não estiver livre, o produtor fica parado esperando
            if instante_buffer_livre > instante_disponivel:
                bloqueio_produtor_ms += instante_buffer_livre - instante_disponivel

            instante_disponivel = max(instante_disponivel, instante_buffer_livre)

        # soma o tempo que leva para produzir o bloco atual
        fim_producao[i] = instante_disponivel + producao_ms
        fim_produtor_anterior = fim_producao[i]

        # o dispositivo só começa quando o bloco estiver pronto
        # e quando tiver terminado de gravar o bloco anterior
        inicio_consumo = max(fim_producao[i], fim_dispositivo_anterior)

        # calcula quando termina a gravação desse bloco
        fim_consumo[i] = inicio_consumo + consumo_ms
        fim_dispositivo_anterior = fim_consumo[i]

    tempo_total_ms = fim_consumo[-1]
    utilizacao_dispositivo_pct = (
        100.0 * (blocos * consumo_ms)/tempo_total_ms
        if tempo_total_ms > 0
        else 0.0
    )

    return {
        "tempo_total_ms": tempo_total_ms,
        "bloqueio_produtor_ms": bloqueio_produtor_ms,
        "utilizacao_dispositivo_pct": utilizacao_dispositivo_pct,
    }