# -*- coding: utf-8 -*-
"""
Integração ponta a ponta (obrigatória para grupos de 4 integrantes).

Ideia: rodar uma carga do SISTEMA DE ARQUIVOS guardando o histórico dos acessos ao disco
(CamadaBloco com guardar_historico=True) e transformar esse histórico numa carga de E/S, que
então passa pela cache (M1) e pelo escalonador, no simulador de E/S. Assim dá para medir
como a organização dos arquivos no disco (alocação, diretórios) afeta o escalonamento e a
cache.

Cada item do histórico é (instante_ms, processo, tipo, bloco, n_blocos).
"""

from simes.es.requisicao import Requisicao


def historico_para_requisicoes(historico):
    """Converte o histórico da camada de blocos em requisições de E/S."""

    requisicoes = []

    # ordeno pelo instante de chegada
    # se duas tiverem o mesmo instante, mantenho a ordem que já estava no histórico
    historico_ordenado = sorted(
        historico,
        key=lambda item: item[0]
    )

    # cada acesso do histórico vira uma requisição de E/S
    for id_requisicao, item in enumerate(historico_ordenado):
        instante_ms, processo, tipo, bloco, n_blocos = item

        requisicao = Requisicao(
            id=id_requisicao,
            chegada=instante_ms,
            processo=processo,
            tipo=tipo,
            bloco=bloco,
            n_blocos=n_blocos,
        )

        requisicoes.append(requisicao)

    return requisicoes
