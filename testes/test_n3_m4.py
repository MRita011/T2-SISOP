# -*- coding: utf-8 -*-
"""Testes complementares do núcleo N3 (sistema de arquivos) e módulo M4 (links)."""
import unittest

from simes.arquivos.estruturas import ErroSA
from simes.arquivos.simulador import montar_sistema


class TesteN3eM4Complementar(unittest.TestCase):
    def test_resolver_raiz_e_seguir_simbolico_false(self):
        sa = montar_sistema("contigua", total_blocos=1000)
        antes = sa.camada.acessos
        self.assertIs(sa.resolver("/"), sa.raiz)
        self.assertEqual(sa.camada.acessos - antes, 0)

        sa.mkdir("P1", "/d")
        sa.create("P1", "/d/arq.txt", 4096)
        sym = sa.symlink("P1", "/d/arq.txt", "/d/atalho")

        self.assertIs(sa.resolver("/d/atalho", seguir_simbolico=False), sym)
        self.assertEqual(sa.resolver("/d/atalho", seguir_simbolico=True).nome, "arq.txt")

    def test_percorrer_separa_links_pendentes_de_eloop(self):
        sa = montar_sistema("contigua", total_blocos=1000)
        sa.mkdir("P1", "/d")
        sa.create("P1", "/d/b.txt", 4096)
        sa.symlink("P1", "/d/b.txt", "/d/b_sym")
        sa.symlink("P1", "/d/l2", "/d/l1")
        sa.symlink("P1", "/d/l1", "/d/l2")

        sa.percorrer("P1", "/")
        self.assertEqual(sa.contadores["links_pendentes"], 0)
        self.assertEqual(sa.contadores["percorrer_diretorios"], 2)
        self.assertEqual(sa.contadores["percorrer_arquivos"], 1)

        sa.unlink("P1", "/d/b.txt")
        with self.assertRaises(ErroSA) as ctx:
            sa.open("P1", "/d/b_sym", "r", "h1")
        self.assertEqual(ctx.exception.codigo, "ENOENT")
        self.assertEqual(sa.contadores["links_pendentes"], 1)

        sa.percorrer("P1", "/")
        self.assertEqual(sa.contadores["links_pendentes"], 2)

    def test_hard_link_custo_persistencia_e_protecao_diretorio(self):
        sa = montar_sistema("contigua", total_blocos=1000)
        sa.mkdir("P1", "/d1")
        sa.mkdir("P1", "/d2")
        sa.create("P1", "/d1/f.txt", 4096)

        antes = (sa.camada.leituras, sa.camada.escritas)
        sa.link("P1", "/d1/f.txt", "/d2/f_hard")
        self.assertEqual((sa.camada.leituras - antes[0], sa.camada.escritas - antes[1]), (4, 1))

        livres_antes = sa.alocador.bitmap.livres()
        sa.unlink("P1", "/d1/f.txt")
        self.assertEqual(sa.alocador.bitmap.livres(), livres_antes)

        sa.open("P1", "/d2/f_hard", "a", "h1")
        sa.write("P1", "h1", 4096)
        sa.close("P1", "h1")
        self.assertEqual(sa.resolver("/d2/f_hard").tamanho, 8192)

        with self.assertRaises(ErroSA) as ctx:
            sa.unlink("P1", "/d2")
        self.assertEqual(ctx.exception.codigo, "EPERM")


if __name__ == "__main__":
    unittest.main()
