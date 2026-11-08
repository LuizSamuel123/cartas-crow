from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import pygame


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COLOR_BG = (24, 28, 38)
COLOR_PANEL = (39, 46, 62)
COLOR_PANEL_LIGHT = (58, 68, 90)
COLOR_TEXT = (235, 239, 245)
COLOR_MUTED = (165, 173, 190)
COLOR_ACCENT = (255, 211, 105)
COLOR_AVATAR = (89, 160, 255)
COLOR_CORPO = (118, 214, 147)
COLOR_PODER = (218, 122, 255)
COLOR_DANGER = (255, 113, 113)
COLOR_BUTTON = (88, 120, 188)
COLOR_BUTTON_HOVER = (105, 142, 220)
COLOR_BUTTON_DISABLED = (74, 78, 90)
COLOR_BLACK = (8, 10, 14)


def carregar_imagem_ajustada(caminho: str, tamanho: tuple[int, int]) -> pygame.Surface | None:
    """Carrega uma imagem com transparencia sem distorcer sua proporcao."""
    if not os.path.isabs(caminho):
        caminho = os.path.join(BASE_DIR, caminho)

    try:
        imagem = pygame.image.load(caminho).convert_alpha()
    except (FileNotFoundError, pygame.error):
        return None

    largura, altura = imagem.get_size()
    escala = min(tamanho[0] / largura, tamanho[1] / altura)
    novo_tamanho = (max(1, round(largura * escala)), max(1, round(altura * escala)))
    imagem = pygame.transform.scale(imagem, novo_tamanho)

    canvas = pygame.Surface(tamanho, pygame.SRCALPHA)
    posicao = ((tamanho[0] - novo_tamanho[0]) // 2, (tamanho[1] - novo_tamanho[1]) // 2)
    canvas.blit(imagem, posicao)
    return canvas


@dataclass(frozen=True)
class Carta:
    """Representa uma carta individual usada como parte da fusao."""

    nome: str
    tipo: str  # avatar, corpo ou poder
    caminho_imagem: str


@dataclass(frozen=True)
class MonstroFusao:
    """Representa o monstro criado ao combinar Avatar + Corpo + Poder."""

    nome: str
    atk: int
    defesa: int
    caminho_imagem: str


class SistemaDeFusao:
    """Centraliza as receitas de fusao disponiveis no jogo."""

    def __init__(self) -> None:
        self._receitas: dict[tuple[str, str, str], MonstroFusao] = {
            ("Elefante", "Diamante", "Gelo"): MonstroFusao(
                nome="Elefante Diamantino do Gelo",
                atk=2500,
                defesa=3000,
                caminho_imagem=os.path.join("artes", "elefante_diamante_gelo.png"),
            )
        }

    def fundir(self, avatar: Carta, corpo: Carta, poder: Carta) -> MonstroFusao | None:
        chave = (avatar.nome, corpo.nome, poder.nome)
        return self._receitas.get(chave)


class Botao:
    """Botao simples com estado hover e habilitado/desabilitado."""

    def __init__(self, rect: pygame.Rect, texto: str, font: pygame.font.Font) -> None:
        self.rect = rect
        self.texto = texto
        self.font = font

    def desenhar(self, surface: pygame.Surface, habilitado: bool) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)
        color = COLOR_BUTTON_DISABLED
        if habilitado:
            color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON

        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_BLACK, self.rect, width=3, border_radius=6)

        texto = self.font.render(self.texto, True, COLOR_TEXT if habilitado else COLOR_MUTED)
        texto_rect = texto.get_rect(center=self.rect.center)
        surface.blit(texto, texto_rect)

    def clicado(self, event: pygame.event.Event, habilitado: bool) -> bool:
        return (
            habilitado
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class SlotSelecao:
    """Area clicavel que representa uma carta da mao do jogador."""

    CORES_TIPO = {
        "avatar": COLOR_AVATAR,
        "corpo": COLOR_CORPO,
        "poder": COLOR_PODER,
    }

    def __init__(self, carta: Carta, rect: pygame.Rect, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.carta = carta
        self.rect = rect
        self.font = font
        self.small_font = small_font
        self.selecionado = False
        self.imagem = carregar_imagem_ajustada(self.carta.caminho_imagem, (62, 58))

    def alternar(self) -> None:
        self.selecionado = not self.selecionado

    def processar_evento(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.alternar()

    def desenhar(self, surface: pygame.Surface) -> None:
        tipo_color = self.CORES_TIPO.get(self.carta.tipo, COLOR_PANEL_LIGHT)
        border_color = COLOR_ACCENT if self.selecionado else COLOR_BLACK

        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, width=4, border_radius=6)

        stripe = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 26)
        pygame.draw.rect(surface, tipo_color, stripe, border_radius=6)
        pygame.draw.rect(surface, tipo_color, (stripe.x, stripe.bottom - 6, stripe.width, 6))

        tipo_texto = self.small_font.render(self.carta.tipo.upper(), True, COLOR_BLACK)
        tipo_rect = tipo_texto.get_rect(center=stripe.center)
        surface.blit(tipo_texto, tipo_rect)

        if self.imagem is not None:
            imagem_rect = self.imagem.get_rect(center=(self.rect.x + 42, self.rect.y + 62))
            surface.blit(self.imagem, imagem_rect)

        nome = self.font.render(self.carta.nome, True, COLOR_TEXT)
        nome_rect = nome.get_rect(center=(self.rect.x + 116, self.rect.y + 60))
        surface.blit(nome, nome_rect)

        status = "SELECIONADA" if self.selecionado else "CLIQUE"
        status_color = COLOR_ACCENT if self.selecionado else COLOR_MUTED
        status_texto = self.small_font.render(status, True, status_color)
        status_rect = status_texto.get_rect(center=(self.rect.centerx, self.rect.bottom - 18))
        surface.blit(status_texto, status_rect)


class JogoFusao:
    """Controla janela, eventos, desenho e estado principal do MVP."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("MVP - Card Game de Fusao Modular")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.Font(None, 34)
        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 20)
        self.font_big = pygame.font.Font(None, 42)

        self.sistema_fusao = SistemaDeFusao()
        self.monstro_resultado: MonstroFusao | None = None
        self.mensagem = "Selecione Avatar, Corpo e Poder para revelar a fusao."

        self.slots = self._criar_slots()
        self.botao_fundir = Botao(
            pygame.Rect((SCREEN_WIDTH - 180) // 2, 405, 180, 52),
            "FUNDIR",
            self.font_title,
        )

    def _criar_slots(self) -> list[SlotSelecao]:
        cartas = [
            Carta("Elefante", "avatar", os.path.join("artes", "elefante.png")),
            Carta("Diamante", "corpo", os.path.join("artes", "diamante.png")),
            Carta("Gelo", "poder", os.path.join("artes", "gelo.png")),
        ]

        largura = 170
        altura = 120
        espacamento = 30
        inicio_x = (SCREEN_WIDTH - (largura * 3 + espacamento * 2)) // 2
        y = 465

        return [
            SlotSelecao(carta, pygame.Rect(inicio_x + index * (largura + espacamento), y, largura, altura), self.font, self.font_small)
            for index, carta in enumerate(cartas)
        ]

    def executar(self) -> None:
        rodando = True
        while rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
                self._processar_evento(event)

            self._desenhar()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def _processar_evento(self, event: pygame.event.Event) -> None:
        for slot in self.slots:
            slot.processar_evento(event)

        if self.botao_fundir.clicado(event, self._pode_fundir()):
            self._tentar_fusao()

    def _pode_fundir(self) -> bool:
        tipos_necessarios = {"avatar", "corpo", "poder"}
        tipos_selecionados = {slot.carta.tipo for slot in self.slots if slot.selecionado}
        return tipos_necessarios == tipos_selecionados

    def _tentar_fusao(self) -> None:
        cartas = {slot.carta.tipo: slot.carta for slot in self.slots if slot.selecionado}
        resultado = self.sistema_fusao.fundir(cartas["avatar"], cartas["corpo"], cartas["poder"])

        if resultado is None:
            self.monstro_resultado = None
            self.mensagem = "Essa combinacao ainda nao possui receita cadastrada."
            return

        self.monstro_resultado = resultado
        self.mensagem = "Fusao concluida!"

    def _desenhar(self) -> None:
        self.screen.fill(COLOR_BG)
        self._desenhar_cabecalho()
        self._desenhar_area_resultado()
        self._desenhar_mensagem()
        self.botao_fundir.desenhar(self.screen, self._pode_fundir())

        for slot in self.slots:
            slot.desenhar(self.screen)

    def _desenhar_cabecalho(self) -> None:
        titulo = self.font_big.render("Card Game de Fusao Modular", True, COLOR_TEXT)
        titulo_rect = titulo.get_rect(center=(SCREEN_WIDTH // 2, 32))
        self.screen.blit(titulo, titulo_rect)

        subtitulo = self.font.render("MVP offline em Python + Pygame", True, COLOR_MUTED)
        subtitulo_rect = subtitulo.get_rect(center=(SCREEN_WIDTH // 2, 64))
        self.screen.blit(subtitulo, subtitulo_rect)

    def _desenhar_area_resultado(self) -> None:
        area = pygame.Rect(230, 92, 340, 288)
        pygame.draw.rect(self.screen, COLOR_PANEL, area, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BLACK, area, width=4, border_radius=8)

        if self.monstro_resultado is None:
            self._desenhar_placeholder_vazio(area)
            return

        self._desenhar_monstro(area, self.monstro_resultado)

    def _desenhar_placeholder_vazio(self, area: pygame.Rect) -> None:
        centro = area.center
        icon_rect = pygame.Rect(0, 0, 170, 150)
        icon_rect.center = (centro[0], centro[1] - 25)

        pygame.draw.rect(self.screen, COLOR_PANEL_LIGHT, icon_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ACCENT, icon_rect, width=3, border_radius=6)

        texto = self.font.render("Fusao aguardando", True, COLOR_TEXT)
        texto_rect = texto.get_rect(center=(centro[0], icon_rect.bottom + 28))
        self.screen.blit(texto, texto_rect)

        dica = self.font_small.render("Selecione as 3 cartas e clique em FUNDIR", True, COLOR_MUTED)
        dica_rect = dica.get_rect(center=(centro[0], icon_rect.bottom + 52))
        self.screen.blit(dica, dica_rect)

    def _desenhar_monstro(self, area: pygame.Rect, monstro: MonstroFusao) -> None:
        imagem_area = pygame.Rect(area.x + 85, area.y + 18, 170, 150)
        imagem = self._carregar_imagem(monstro.caminho_imagem, imagem_area.size)

        if imagem is None:
            self._desenhar_imagem_substituta(imagem_area)
        else:
            self.screen.blit(imagem, imagem_area)
            pygame.draw.rect(self.screen, COLOR_ACCENT, imagem_area, width=3, border_radius=6)

        nome = self._render_multilinha(monstro.nome, self.font_title, COLOR_TEXT, area.width - 42)
        y_nome = imagem_area.bottom + 16
        for linha in nome:
            linha_rect = linha.get_rect(center=(area.centerx, y_nome))
            self.screen.blit(linha, linha_rect)
            y_nome += 28

        stats_texto = self.font.render(f"ATK {monstro.atk}   DEF {monstro.defesa}", True, COLOR_ACCENT)
        stats_rect = stats_texto.get_rect(center=(area.centerx, area.bottom - 28))
        self.screen.blit(stats_texto, stats_rect)

    def _carregar_imagem(self, caminho: str, tamanho: tuple[int, int]) -> pygame.Surface | None:
        return carregar_imagem_ajustada(caminho, tamanho)

    def _desenhar_imagem_substituta(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (74, 94, 126), rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ACCENT, rect, width=3, border_radius=6)

        pygame.draw.circle(self.screen, (180, 220, 255), (rect.centerx, rect.y + 52), 36)
        pygame.draw.rect(self.screen, (190, 210, 230), (rect.centerx - 52, rect.y + 82, 104, 40), border_radius=8)
        pygame.draw.polygon(
            self.screen,
            (120, 180, 255),
            [
                (rect.centerx - 35, rect.y + 36),
                (rect.centerx - 15, rect.y + 18),
                (rect.centerx - 5, rect.y + 46),
            ],
        )
        pygame.draw.polygon(
            self.screen,
            (120, 180, 255),
            [
                (rect.centerx + 35, rect.y + 36),
                (rect.centerx + 15, rect.y + 18),
                (rect.centerx + 5, rect.y + 46),
            ],
        )

        aviso = self.font_small.render("arte nao encontrada", True, COLOR_TEXT)
        aviso_rect = aviso.get_rect(center=(rect.centerx, rect.bottom - 16))
        self.screen.blit(aviso, aviso_rect)

    def _desenhar_mensagem(self) -> None:
        texto = self.font.render(self.mensagem, True, COLOR_TEXT if self.monstro_resultado else COLOR_MUTED)
        texto_rect = texto.get_rect(center=(SCREEN_WIDTH // 2, 392))
        self.screen.blit(texto, texto_rect)

    @staticmethod
    def _render_multilinha(texto: str, font: pygame.font.Font, cor: tuple[int, int, int], largura_max: int) -> list[pygame.Surface]:
        palavras = texto.split()
        linhas: list[str] = []
        linha_atual = ""

        for palavra in palavras:
            tentativa = palavra if not linha_atual else f"{linha_atual} {palavra}"
            if font.size(tentativa)[0] <= largura_max:
                linha_atual = tentativa
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)

        return [font.render(linha, True, cor) for linha in linhas]


if __name__ == "__main__":
    JogoFusao().executar()
