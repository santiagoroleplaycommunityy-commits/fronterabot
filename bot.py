import discord
from discord.ext import commands
import asyncio
import io
import os
from dotenv import load_dotenv

load_dotenv()  # lee .env en tu PC; en Railway usa las variables del panel
TOKEN = os.getenv("MTU0ODY4ODIyOTY3MzQ3MjA1MQ.GpKGtx.d5ldDjPdZ_a22dF4Wz_mLl8HqDBtsaeYjnHYu4")

# ...todo tu código...

bot.run(TOKEN)

intents = discord.Intents.default()
intents.message_content = True  # necesario para los comandos con !

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()  # sincroniza los slash commands
    print(f"Bot conectado como {bot.user}")

@bot.hybrid_command(name="ejemplo", description="Comando de ejemplo")
async def ejemplo(ctx):
    embed = discord.Embed(
        title="Título",
        description="Descripción",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

import json
import os

import discord
from discord import app_commands
from discord.ext import commands

# ================== CONFIGURACIÓN ==================
TOKEN = "MTU0ODY4ODIyOTY3MzQ3MjA1MQ.GpKGtx.d5ldDjPdZ_a22dF4Wz_mLl8HqDBtsaeYjnHYu4"
ROL_STAFF_ID = 1541949119197872142
CANAL_URL = "https://discord.com/channels/1491640463738933349/1541933557880979526"
BANNER_URL = "https://media.discordapp.net/attachments/1499888766968397967/1573126085095198882/CHER_BANNER_1.png?ex=6b00df55&is=6aff8dd5&hm=2d9ae851c4e303d89e6b104268c0a1315726c3be308fd6c686d02ff82893c658&format=webp&quality=lossless"
COLOR_ACENTO = 1843769
ARCHIVO = "encuestas.json"
# ===================================================

# ---------- Guardado de votos (sobrevive reinicios) ----------
def cargar():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar():
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(encuestas, f, indent=2)


encuestas = cargar()  # {"id_mensaje": {"meta": int, "votantes": [ids]}}


def es_staff(usuario) -> bool:
    return any(r.id == ROL_STAFF_ID for r in getattr(usuario, "roles", []))


# ---------- Mensaje de la encuesta ----------
class EncuestaView(discord.ui.LayoutView):
    def __init__(self, datos: dict):
        super().__init__(timeout=None)
        self.datos = datos
        self.construir()

    def construir(self):
        self.clear_items()
        actuales = len(self.datos["votantes"])
        meta = self.datos["meta"]
        completa = actuales >= meta

        boton_votar = discord.ui.Button(
            label="Votar",
            style=discord.ButtonStyle.secondary,
            custom_id="encuesta:votar",
            disabled=completa,
        )
        boton_votar.callback = self.votar

        boton_ver = discord.ui.Button(
            label="Ver Votos",
            style=discord.ButtonStyle.secondary,
            custom_id="encuesta:ver_votos",
        )
        boton_ver.callback = self.ver_votos

        estado = "✅ **¡Meta alcanzada!**" if completa else ""

        texto = (
            "## ENCUESTA DE APERTURA\n"
            "> Informamos a toda nuestra comunidad que se ha abierto una Encuesta de Apertura de servidor.\n\n"
            "> En el momento que la encuesta llegue a los votos deseados por el Departamento Administrativo "
            f"será abierto el servidor en el canal de {CANAL_URL}\n\n"
            "> Si votas tienes que unirte OBLIGATORIAMENTE al servidor de roblox para no ser sancionado\n\n"
            f"**Votos Actuales {actuales}/{meta}** {estado}"
        )

        contenedor = discord.ui.Container(
            discord.ui.TextDisplay("@everyone"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay(texto),
            discord.ui.ActionRow(boton_votar, boton_ver),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.MediaGallery(discord.MediaGalleryItem(BANNER_URL)),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay("Mayson Studios Todos sus derechos reservados © 2026"),
            accent_colour=COLOR_ACENTO,
        )
        self.add_item(contenedor)

    async def votar(self, interaction: discord.Interaction):
        uid = interaction.user.id

        if uid in self.datos["votantes"]:
            return await interaction.response.send_message(
                "⚠️ Ya registraste tu voto en esta encuesta.", ephemeral=True
            )
        if len(self.datos["votantes"]) >= self.datos["meta"]:
            return await interaction.response.send_message(
                "⚠️ La encuesta ya alcanzó la meta de votos.", ephemeral=True
            )

        self.datos["votantes"].append(uid)
        guardar()

        self.construir()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "✅ ¡Tu voto fue registrado! Recuerda unirte al servidor de Roblox.",
            ephemeral=True,
        )

    async def ver_votos(self, interaction: discord.Interaction):
        if not es_staff(interaction.user):
            return await interaction.response.send_message(
                "❌ Solo el staff puede ver la lista de votos.", ephemeral=True
            )

        votantes = self.datos["votantes"]
        if not votantes:
            return await interaction.response.send_message(
                "📭 Todavía nadie ha votado.", ephemeral=True
            )

        lineas = [f"{i}. <@{uid}>" for i, uid in enumerate(votantes, start=1)]
        encabezado = f"**Votos: {len(votantes)}/{self.datos['meta']}**\n"

        # Dividir en partes por el límite de 2000 caracteres de Discord
        partes, actual = [], encabezado
        for linea in lineas:
            if len(actual) + len(linea) + 1 > 1900:
                partes.append(actual)
                actual = ""
            actual += linea + "\n"
        partes.append(actual)

        await interaction.response.send_message(partes[0], ephemeral=True)
        for parte in partes[1:]:
            await interaction.followup.send(parte, ephemeral=True)


# ---------- Bot ----------
class MiBot(commands.Bot):
    async def setup_hook(self):
        # Reactiva los botones de encuestas anteriores tras reiniciar el bot
        for msg_id, datos in encuestas.items():
            self.add_view(EncuestaView(datos), message_id=int(msg_id))
        await self.tree.sync()


intents = discord.Intents.default()
intents.message_content = True
bot = MiBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


@bot.hybrid_command(name="encuesta", description="Abre una encuesta de apertura de servidor")
@app_commands.describe(votos="Cantidad de votos que se desea alcanzar")
@commands.has_role(ROL_STAFF_ID)
async def encuesta(ctx: commands.Context, votos: int):
    if votos < 1:
        return await ctx.send("❌ El monto de votos debe ser mayor a 0.", ephemeral=True)

    datos = {"meta": votos, "votantes": []}
    view = EncuestaView(datos)

    mensaje = await ctx.send(
        view=view,
        allowed_mentions=discord.AllowedMentions(everyone=True),
    )

    encuestas[str(mensaje.id)] = datos
    guardar()

    # Borra el !encuesta escrito por el staff para que quede limpio
    if ctx.interaction is None:
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


@encuesta.error
async def encuesta_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Solo el staff puede usar este comando.", ephemeral=True)
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send("Uso correcto: `!encuesta <cantidad de votos>`", ephemeral=True)
    else:
        raise error
class MiBot(commands.Bot):
    async def setup_hook(self):
        # Encuestas
        for msg_id, datos in encuestas.items():
            self.add_view(EncuestaView(datos), message_id=int(msg_id))
        # Panel y tickets
        self.add_view(PanelView())
        for datos in db_tickets["tickets"].values():
            if datos.get("mensaje_id"):
                self.add_view(TicketView(datos), message_id=datos["mensaje_id"])
        await self.tree.sync()


# ======================================================
#                 SISTEMA DE TICKETS
# ======================================================
NOMBRE_CATEGORIA = "🎫 TICKETS"      # categoría privada que se crea sola
LOG_CANAL_ID = 0                      # ID de un canal de logs (0 = sin transcripciones)
BANNER_TICKETS_URL = "https://media.discordapp.net/attachments/1499888766968397967/1573129022257500290/CHER_BANNER_2.png?ex=6b00e212&is=6aff9092&hm=0bdd5b828383f3b6cb66b7f87d053e3e580273da10591840bc5f3cdbad6d854b&format=webp&quality=lossless"
ARCHIVO_TICKETS = "tickets.json"
FOOTER = "Mayson Studios Todos sus derechos reservados © 2026"

CORTO = discord.TextStyle.short
LARGO = discord.TextStyle.paragraph

# Cada pregunta: (etiqueta, estilo, largo máximo, obligatoria, placeholder)
CATEGORIAS = {
    "soporte": {
        "nombre": "Soporte General",
        "slug": "soporte-general",
        "emoji": "🛠️",
        "descripcion": "Problemas, consultas o inconvenientes",
        "preguntas": [
            ("Asunto", CORTO, 100, True, "Resumen breve de tu consulta"),
            ("Describe tu inconveniente", LARGO, 600, True, "Explica con el mayor detalle posible"),
            ("¿Qué has intentado para solucionarlo?", LARGO, 400, False, "Pasos que ya probaste"),
        ],
    },
    "postulaciones": {
        "nombre": "Postulaciones",
        "slug": "postulaciones",
        "emoji": "📋",
        "descripcion": "Procesos de selección institucional o administrativa",
        "preguntas": [
            ("¿A qué proceso postulas?", CORTO, 100, True, "Ej: Carabineros, PDI, Administración..."),
            ("Tu usuario de Roblox", CORTO, 100, True, "Nombre exacto de tu cuenta"),
            ("Cuéntanos sobre ti y tu experiencia", LARGO, 600, True, "Experiencia en roleplay, cargos anteriores, etc."),
            ("¿Por qué deseas postular?", LARGO, 500, True, "Tus motivos y qué puedes aportar"),
        ],
    },
    "reportes": {
        "nombre": "Reportes",
        "slug": "reportes",
        "emoji": "📢",
        "descripcion": "Conductas indebidas o incumplimiento de normativa",
        "preguntas": [
            ("Usuario(s) reportado(s)", CORTO, 100, True, "Nombre de Roblox / Discord"),
            ("Normativa incumplida", LARGO, 400, True, "¿Qué norma se rompió?"),
            ("Descripción de lo ocurrido", LARGO, 600, True, "Cuenta lo sucedido paso a paso"),
            ("Pruebas (links de imágenes o videos)", CORTO, 300, False, "También puedes adjuntarlas en el ticket"),
            ("Fecha y hora aproximada", CORTO, 100, False, "Ej: 19/11 a las 21:30"),
        ],
    },
    "alianzas": {
        "nombre": "Alianzas",
        "slug": "alianzas",
        "emoji": "🤝",
        "descripcion": "Propuestas de colaboración con otras comunidades",
        "preguntas": [
            ("Nombre de tu comunidad", CORTO, 100, True, "Nombre del servidor"),
            ("Enlace de invitación", CORTO, 200, True, "https://discord.gg/..."),
            ("Cantidad de miembros", CORTO, 50, True, "Ej: 500"),
            ("Propuesta de alianza", LARGO, 600, True, "¿Qué ofreces y qué buscas?"),
        ],
    },
    "gestion": {
        "nombre": "Gestión Administrativa",
        "slug": "gestion-administrativa",
        "emoji": "📁",
        "descripcion": "Solicitudes y asuntos de la administración",
        "preguntas": [
            ("Asunto", CORTO, 100, True, "Resumen breve de tu solicitud"),
            ("Tipo de solicitud", CORTO, 100, True, "Ej: Rango, sanción, apelación, permisos..."),
            ("Detalle de tu solicitud", LARGO, 700, True, "Explica con claridad lo que necesitas"),
        ],
    },
}

TEXTO_PANEL = (
    "## Centro de Atención | La Frontera Roleplay\n\n"
    "Bienvenido al centro de atención oficial de **La Frontera Roleplay**.\n\n"
    "Mediante este sistema podrás comunicarte directamente con nuestro equipo administrativo para realizar "
    "consultas, solicitar asistencia o gestionar diferentes requerimientos relacionados con el servidor.\n\n"
    "**Categorías disponibles:**\n\n"
    "- **Soporte General:** Problemas, consultas o inconvenientes dentro del servidor.\n"
    "- **Reportes:** Informar conductas indebidas o incumplimientos de la normativa.\n"
    "- **Postulaciones:** Consultas relacionadas con procesos de selección institucional o administrativa.\n"
    "- **Alianzas:** Propuestas de colaboración con otras comunidades.\n"
    "- **Gestión Administrativa:** Solicitudes y asuntos relacionados con la administración del servidor.\n\n"
    "Selecciona la categoría correspondiente para generar un ticket y recibir atención por parte del "
    "departamento encargado.\n\n"
    "**Importante:** Proporciona información clara y detallada sobre tu solicitud. Evita abrir múltiples "
    "tickets por un mismo asunto y mantén siempre un trato respetuoso hacia nuestro equipo.\n\n"
    "**La Frontera Roleplay**\n"
)


# ---------- Guardado de datos ----------
def cargar_tickets():
    if os.path.exists(ARCHIVO_TICKETS):
        with open(ARCHIVO_TICKETS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"contador": 0, "tickets": {}}


def guardar_tickets():
    with open(ARCHIVO_TICKETS, "w", encoding="utf-8") as f:
        json.dump(db_tickets, f, indent=2, ensure_ascii=False)


db_tickets = cargar_tickets()  # {"contador": n, "tickets": {id_canal: {...}}}


def ticket_abierto(usuario_id: int, clave: str):
    for canal_id, t in db_tickets["tickets"].items():
        if t["usuario_id"] == usuario_id and t["clave"] == clave:
            return int(canal_id)
    return None


async def obtener_categoria(guild: discord.Guild, rol_staff: discord.Role):
    categoria = discord.utils.get(guild.categories, name=NOMBRE_CATEGORIA)
    if categoria:
        return categoria
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        rol_staff: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True,
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            manage_channels=True, manage_permissions=True,
        ),
    }
    return await guild.create_category(NOMBRE_CATEGORIA, overwrites=overwrites)


# ---------- Formulario (modal) ----------
class TicketModal(discord.ui.Modal):
    def __init__(self, clave: str):
        cat = CATEGORIAS[clave]
        super().__init__(title=f"Ticket | {cat['nombre']}"[:45])
        self.clave = clave
        self.campos = []
        for etiqueta, estilo, maximo, obligatorio, placeholder in cat["preguntas"]:
            campo = discord.ui.TextInput(
                label=etiqueta, style=estilo, max_length=maximo,
                required=obligatorio, placeholder=placeholder,
            )
            self.add_item(campo)
            self.campos.append(campo)

    async def on_submit(self, interaction: discord.Interaction):
        respuestas = [[c.label, c.value or "*Sin respuesta*"] for c in self.campos]
        await crear_ticket(interaction, self.clave, respuestas)


# ---------- Creación del ticket ----------
async def crear_ticket(interaction: discord.Interaction, clave: str, respuestas: list):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    usuario = interaction.user
    cat = CATEGORIAS[clave]

    rol_staff = guild.get_role(ROL_STAFF_ID)
    if rol_staff is None:
        return await interaction.followup.send("❌ No encontré el rol de staff. Avisa a un administrador.", ephemeral=True)

    try:
        categoria = await obtener_categoria(guild, rol_staff)

        db_tickets["contador"] += 1
        numero = db_tickets["contador"]
        nombre = f"ticket-{numero:04d}-{cat['slug']}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            usuario: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True,
            ),
            rol_staff: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                manage_channels=True, manage_permissions=True,
            ),
        }
        canal = await guild.create_text_channel(
            name=nombre, category=categoria, overwrites=overwrites,
            topic=f"Ticket #{numero:04d} | {cat['nombre']} | Usuario: {usuario} ({usuario.id})",
        )
    except discord.Forbidden:
        return await interaction.followup.send(
            "❌ No tengo permisos para crear canales. Avisa a un administrador.", ephemeral=True
        )

    datos = {
        "numero": numero,
        "usuario_id": usuario.id,
        "clave": clave,
        "respuestas": respuestas,
        "reclamado_por": None,
        "mensaje_id": None,
    }
    db_tickets["tickets"][str(canal.id)] = datos
    guardar_tickets()

    mensaje = await canal.send(
        view=TicketView(datos),
        allowed_mentions=discord.AllowedMentions(users=True, roles=True),
    )
    datos["mensaje_id"] = mensaje.id
    guardar_tickets()

    await interaction.followup.send(f"✅ Tu ticket fue creado: {canal.mention}", ephemeral=True)


# ---------- Mensaje dentro del ticket ----------
class TicketView(discord.ui.LayoutView):
    def __init__(self, datos: dict):
        super().__init__(timeout=None)
        self.datos = datos
        self.construir()

    def construir(self):
        self.clear_items()
        d = self.datos
        cat = CATEGORIAS[d["clave"]]
        atendido = f"<@{d['reclamado_por']}>" if d["reclamado_por"] else "Sin reclamar"
        respuestas = "\n\n".join(f"**{p}**\n{r}" for p, r in d["respuestas"])

        boton_reclamar = discord.ui.Button(
            label="Reclamar", emoji="🙋", style=discord.ButtonStyle.success,
            custom_id="ticket:reclamar", disabled=bool(d["reclamado_por"]),
        )
        boton_reclamar.callback = self.reclamar

        boton_cerrar = discord.ui.Button(
            label="Cerrar Ticket", emoji="🔒", style=discord.ButtonStyle.danger,
            custom_id="ticket:cerrar",
        )
        boton_cerrar.callback = self.cerrar

        contenedor = discord.ui.Container(
            discord.ui.TextDisplay(f"<@{d['usuario_id']}> <@&{ROL_STAFF_ID}>"),
            discord.ui.TextDisplay(
                f"## {cat['emoji']} Ticket #{d['numero']:04d} | {cat['nombre']}\n"
                f"**Creado por:** <@{d['usuario_id']}>\n"
                f"**Atendido por:** {atendido}\n\n"
                "Un miembro del equipo te atenderá lo antes posible. "
                "Mientras tanto, puedes agregar más información o pruebas en este canal."
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay(respuestas),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.ActionRow(boton_reclamar, boton_cerrar),
            discord.ui.TextDisplay("**CHILE ETERNO ROLEPLAY**\n" + FOOTER),
            accent_colour=COLOR_ACENTO,
        )
        self.add_item(contenedor)

    async def reclamar(self, interaction: discord.Interaction):
        if not es_staff(interaction.user):
            return await interaction.response.send_message("❌ Solo el staff puede reclamar tickets.", ephemeral=True)
        self.datos["reclamado_por"] = interaction.user.id
        guardar_tickets()
        self.construir()
        await interaction.response.edit_message(view=self)

    async def cerrar(self, interaction: discord.Interaction):
        if not es_staff(interaction.user):
            return await interaction.response.send_message("❌ Solo el staff puede cerrar tickets.", ephemeral=True)

        canal = interaction.channel
        await interaction.response.send_message("🔒 Este ticket se cerrará en 5 segundos...")
        await enviar_transcripcion(canal, interaction.user, self.datos)
        await asyncio.sleep(5)

        db_tickets["tickets"].pop(str(canal.id), None)
        guardar_tickets()
        try:
            await canal.delete(reason=f"Ticket cerrado por {interaction.user}")
        except discord.HTTPException:
            pass


async def enviar_transcripcion(canal: discord.TextChannel, cerrado_por: discord.Member, datos: dict):
    if not LOG_CANAL_ID:
        return
    log = canal.guild.get_channel(LOG_CANAL_ID)
    if log is None:
        return
    try:
        lineas = []
        async for m in canal.history(limit=None, oldest_first=True):
            contenido = m.content or ""
            if m.attachments:
                contenido += " [adjuntos: " + ", ".join(a.url for a in m.attachments) + "]"
            if contenido.strip():
                lineas.append(f"[{m.created_at.strftime('%Y-%m-%d %H:%M')}] {m.author}: {contenido}")
        texto = "\n".join(lineas) or "Sin mensajes."
        archivo = discord.File(io.BytesIO(texto.encode("utf-8")), filename=f"{canal.name}.txt")
        await log.send(
            f"📁 Ticket **{canal.name}** cerrado por {cerrado_por.mention} | Abierto por <@{datos['usuario_id']}>",
            file=archivo,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except discord.HTTPException:
        pass


# ---------- Panel principal ----------
class PanelView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        select = discord.ui.Select(
            placeholder="Categoría de Soporte",
            custom_id="panel:categoria",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=c["nombre"], value=k, emoji=c["emoji"], description=c["descripcion"])
                for k, c in CATEGORIAS.items()
            ],
        )
        select.callback = self.seleccionar

        contenedor = discord.ui.Container(
            discord.ui.TextDisplay(TEXTO_PANEL),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.ActionRow(select),
            discord.ui.TextDisplay(FOOTER),
            discord.ui.MediaGallery(discord.MediaGalleryItem(BANNER_TICKETS_URL)),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            accent_colour=COLOR_ACENTO,
        )
        self.add_item(contenedor)

    async def seleccionar(self, interaction: discord.Interaction):
        clave = interaction.data["values"][0]

        existente = ticket_abierto(interaction.user.id, clave)
        if existente and interaction.guild.get_channel(existente):
            await interaction.response.send_message(
                f"⚠️ Ya tienes un ticket abierto en esta categoría: <#{existente}>", ephemeral=True
            )
        else:
            await interaction.response.send_modal(TicketModal(clave))

        # Reinicia el menú para que no quede la opción marcada
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass


@bot.event
async def on_guild_channel_delete(channel):
    # Si borran un ticket a mano, se libera para que el usuario pueda abrir otro
    if db_tickets["tickets"].pop(str(channel.id), None) is not None:
        guardar_tickets()


@bot.hybrid_command(name="panel", description="Envía el panel de tickets a este canal")
@commands.has_role(ROL_STAFF_ID)
async def panel(ctx: commands.Context):
    await ctx.channel.send(view=PanelView())
    if ctx.interaction:
        await ctx.send("✅ Panel enviado.", ephemeral=True)
    else:
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


@panel.error
async def panel_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Solo el staff puede usar este comando.", ephemeral=True)
    else:
        raise error


# ======================================================
#                   FIN DE TICKETS
# ======================================================


# ======================================================
#                  COMANDO DE CIERRE
# ======================================================
BANNER_CIERRE_URL = "https://media.discordapp.net/attachments/1499888766968397967/1573354624721748038/BANNER_EMBED.png?ex=6b01b42e&is=6b0062ae&hm=889b3ead3c8a6bef0f98552c43828fe3ec12898a64ab43bcfe63ade74fe32c89&format=webp&quality=lossless&width=1280&height=54"

TEXTO_CIERRE = (
    "## LFRP| Cierre de Sesión\n\n"
    "**Se informa a toda nuestra comunidad que la sesión de Roleplay ha finalizado oficialmente.**\n\n"
    "> Agradecemos a todos los ciudadanos, instituciones y miembros del equipo administrativo que "
    "participaron durante la jornada y contribuyeron al desarrollo de las actividades dentro del servidor.\n\n"
    "**Estado del servidor:** CERRADO\n\n"
    "> Las próximas sesiones serán anunciadas oportunamente a través de nuestros canales oficiales de comunicación.\n\n"
    "> Solicitamos a toda la comunidad mantenerse atenta a los próximos comunicados y actualizaciones.\n\n"
    "**Agradecemos su participación y compromiso con Chile Eterno Roleplay.**\n\n"
)


class CierreView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        contenedor = discord.ui.Container(
            discord.ui.TextDisplay(TEXTO_CIERRE),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.MediaGallery(discord.MediaGalleryItem(BANNER_CIERRE_URL)),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay("*Mayson Studios Todos sus derechos reservados © 2026*"),
            accent_colour=COLOR_ACENTO,
        )
        self.add_item(contenedor)


@bot.hybrid_command(name="cierre", description="Anuncia el cierre de una sesión de roleplay")
@commands.has_role(ROL_STAFF_ID)
async def cierre(ctx: commands.Context):
    await ctx.channel.send(view=CierreView())
    if ctx.interaction:
        await ctx.send("✅ Cierre de sesión anunciado.", ephemeral=True)
    else:
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


@cierre.error
async def cierre_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Solo el staff puede usar este comando.", ephemeral=True)
    else:
        raise error


# ======================================================
#                FIN COMANDO DE CIERRE
# ======================================================
bot.run("MTU0ODY4ODIyOTY3MzQ3MjA1MQ.GpKGtx.d5ldDjPdZ_a22dF4Wz_mLl8HqDBtsaeYjnHYu4")