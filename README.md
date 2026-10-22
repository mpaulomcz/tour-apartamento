# Tour 3D · Apartamento de três suítes

Tour virtual publicado pelo GitHub Pages: **https://mpaulomcz.github.io/tour-apartamento/**

O visitante abre na planta, que vira apartamento sozinha, e toca em **Começar a visita**. Dentro, ele anda pelos ambientes com os botões **Anterior / Próximo**, as setas na tela, os marcadores nas portas ou tocando no piso. Parado em cada um dos 11 ambientes, ele vê uma **foto 360° fotorrealista** renderizada no Blender. Ao começar a andar, a foto se funde de volta ao 3D em tempo real.

## Link direto para um ambiente

Acrescente o nome do ambiente depois de `#` para abrir o tour já dentro dele. É útil para o corretor mandar só o que interessa ao cliente:

| Ambiente | Link |
|---|---|
| Hall de entrada | `…/tour-apartamento/#hall-de-entrada` |
| Sala de jantar | `…/#sala-de-jantar` |
| Sala de estar | `…/#sala-de-estar` |
| Cozinha | `…/#cozinha` |
| Área de serviço | `…/#area-de-servico` |
| Varanda gourmet | `…/#varanda-gourmet` |
| Suíte 2 | `…/#suite-2` |
| Suíte 1 | `…/#suite-1` |
| Suíte master | `…/#suite-master` |
| Banho master | `…/#banho-master` |
| Varanda master | `…/#varanda-master` |

O botão **Compartilhar**, no topo, já gera o link do ambiente em que a pessoa está.

## Configuração sem programar: `config.json`

Edite o arquivo `config.json` aqui no GitHub (ícone de lápis → *Commit changes*). O site atualiza em cerca de 1 minuto.

```json
{
  "whatsapp": "5582999999999",
  "whatsappMsg": "Olá! Vi o tour 3D e quero agendar uma visita.",
  "ga4": "G-XXXXXXXXXX",
  "brand": { "name": "Nome da incorporadora", "logo": "logo.png" },
  "areaTotal": 143.7,
  "areas": { "Suíte master + closet": 20.1, "Varanda gourmet": 18.6 },
  "vista": "vista.jpg"
}
```

| Campo | Para que serve |
|---|---|
| `whatsapp` | Número com DDI e DDD, só dígitos. Aparece o botão **Corretor** no topo e **Falar com o corretor no WhatsApp** na abertura. A mensagem já leva o ambiente e o link. |
| `whatsappMsg` | Texto inicial da mensagem (opcional). |
| `ga4` | ID do Google Analytics 4. O tour pede consentimento antes de medir (LGPD) e registra os eventos `tour_start`, `room_view` (com o ambiente), `tour_complete`, `share`, `whatsapp_click`, `night_toggle` e `narration_toggle`. |
| `brand` | Nome e logo (envie o arquivo do logo para a raiz do repositório). |
| `areaTotal`, `areas` | Áreas oficiais do memorial. Quando preenchidas, substituem as medidas aproximadas (o "≈" some). Os nomes dos cômodos são os da planta: `Estar, jantar e cozinha`, `Varanda gourmet`, `Suíte 1 + closet`, `W.C. suíte 1`, `Suíte 2`, `W.C. suíte 2`, `Suíte master + closet`, `W.C. master`, `Varanda master`, `Varanda técnica`, `Área de serviço`, `W.C. serviço`, `Lavabo`. |
| `vista` | Foto panorâmica (equiretangular) da vista real do andar, usada nas janelas do 3D. As fotos 360° precisam ser renderizadas de novo para incluí-la (veja abaixo). |

## Como o tour foi feito (e como repetir para outro apartamento)

Os scripts de referência estão em `ferramentas/`. Eles foram escritos para esta planta e têm ajustes manuais, mas o caminho é o mesmo para qualquer imóvel:

1. **Paredes a partir da planta** (`1_varrer_linhas.py`, `2_extrair_paredes.py`): o script varre a imagem da planta em linhas horizontais e verticais e classifica cada trecho como parede, porta, janela, porta de vidro ou guarda-corpo. As exceções são corrigidas à mão no próprio script.
2. **Cômodos** (`3_comodos.py`): os ambientes são preenchidos a partir das paredes, gerando o polígono e a área em pixels de cada um. A escala vem da largura das portas (80 cm), ou da área oficial de um cômodo.
3. **Texturas** (`4_texturas.py`): mármore, madeiras, tecidos e pisos são gerados por procedimento, em escala real e sem custo de licença.
4. **Mobiliário e pontos de vista**: ficam no código do site (`furniture()` e `VIEWS`). Esta é a etapa manual de cada projeto.
5. **Fotos 360°** (`5_exportar_cena.py` → `6_renderizar_panoramas.py`): a cena do site é exportada em GLB e renderizada no Blender (Cycles) exatamente da posição de cada parada. O render de 2048 px leva uns 10 minutos por ambiente num computador comum.
6. **Montagem** (`7_montar_site.py`): junta tudo, converte as texturas para WebP (com versão reduzida para celular) e gera a pasta publicada.

## Créditos

Áreas aproximadas, medidas a partir da planta baixa. Mobiliário e acabamentos são ilustrativos. HDRIs Lebombo e Wasteland Clouds, Poly Haven (CC0). Poltrona Sheen Chair, Wayfair (CC0). Planta Potted Plant 02, Poly Haven (CC0), versão de Eric Chadwick (CC BY 4.0). Feito com three.js, GSAP e Blender.
