"""Textos por idioma.

Cada idioma aporta los valores por defecto de los textos. Cualquier clave
puede sobrescribirse en config.toml, y se pueden añadir idiomas nuevos con
una sección [locales.<código>] que tenga las mismas claves.
"""

LOCALES: dict = {
    "es": {
        "subtitle": "**{streak}** días de racha · máx. {max_streak} · {active_days} días activos",
        "months": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
        "weekdays": ["L", "", "X", "", "V", "", ""],
        "less": "Menos",
        "more": "Más",
        "footer": "Actualizado {updated}",
        "tooltip": "{count} envíos · {date}",
        "date_format": "%d/%m/%Y",
        "label": "Actividad en LeetCode de {user}",
    },
    "en": {
        "subtitle": "**{streak}** day streak · best {max_streak} · {active_days} active days",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "weekdays": ["Mon", "", "Wed", "", "Fri", "", ""],
        "less": "Less",
        "more": "More",
        "footer": "Updated {updated}",
        "tooltip": "{count} submissions · {date}",
        "date_format": "%Y-%m-%d",
        "label": "LeetCode activity of {user}",
    },
    "fr": {
        "subtitle": "Série de **{streak}** jours · record {max_streak} · {active_days} jours actifs",
        "months": ["Janv", "Févr", "Mars", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"],
        "weekdays": ["Lun", "", "Mer", "", "Ven", "", ""],
        "less": "Moins",
        "more": "Plus",
        "footer": "Mis à jour le {updated}",
        "tooltip": "{count} soumissions · {date}",
        "date_format": "%d/%m/%Y",
        "label": "Activité LeetCode de {user}",
    },
    "de": {
        "subtitle": "**{streak}** Tage in Folge · Rekord {max_streak} · {active_days} aktive Tage",
        "months": ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
        "weekdays": ["Mo", "", "Mi", "", "Fr", "", ""],
        "less": "Weniger",
        "more": "Mehr",
        "footer": "Aktualisiert am {updated}",
        "tooltip": "{count} Einreichungen · {date}",
        "date_format": "%d.%m.%Y",
        "label": "LeetCode-Aktivität von {user}",
    },
    "it": {
        "subtitle": "**{streak}** giorni di fila · record {max_streak} · {active_days} giorni attivi",
        "months": ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"],
        "weekdays": ["Lun", "", "Mer", "", "Ven", "", ""],
        "less": "Meno",
        "more": "Più",
        "footer": "Aggiornato il {updated}",
        "tooltip": "{count} invii · {date}",
        "date_format": "%d/%m/%Y",
        "label": "Attività LeetCode di {user}",
    },
    "pt": {
        "subtitle": "**{streak}** dias seguidos · recorde {max_streak} · {active_days} dias ativos",
        "months": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
        "weekdays": ["Seg", "", "Qua", "", "Sex", "", ""],
        "less": "Menos",
        "more": "Mais",
        "footer": "Atualizado em {updated}",
        "tooltip": "{count} envios · {date}",
        "date_format": "%d/%m/%Y",
        "label": "Atividade no LeetCode de {user}",
    },
    "ca": {
        "subtitle": "**{streak}** dies seguits · rècord {max_streak} · {active_days} dies actius",
        "months": ["Gen", "Feb", "Març", "Abr", "Maig", "Juny", "Jul", "Ag", "Set", "Oct", "Nov", "Des"],
        "weekdays": ["Dl", "", "Dc", "", "Dv", "", ""],
        "less": "Menys",
        "more": "Més",
        "footer": "Actualitzat el {updated}",
        "tooltip": "{count} enviaments · {date}",
        "date_format": "%d/%m/%Y",
        "label": "Activitat a LeetCode de {user}",
    },
    "ja": {
        "subtitle": "連続 **{streak}** 日 · 最長 {max_streak} 日 · 活動日数 {active_days}",
        "months": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
        "weekdays": ["月", "", "水", "", "金", "", ""],
        "less": "少",
        "more": "多",
        "footer": "{updated} 更新",
        "tooltip": "{date} · {count} 件",
        "date_format": "%Y/%m/%d",
        "label": "{user} の LeetCode アクティビティ",
    },
}


def as_config(texts: dict) -> dict:
    """Convierte los textos de un idioma en claves de configuración."""
    return {
        "subtitle": {"text": texts["subtitle"]},
        "months": {"names": texts["months"]},
        "weekdays": {"labels": texts["weekdays"]},
        "legend": {"less": texts["less"], "more": texts["more"]},
        "footer": {"text": texts["footer"]},
        "tooltip": {"text": texts["tooltip"], "date_format": texts["date_format"]},
        "label": texts["label"],
    }
