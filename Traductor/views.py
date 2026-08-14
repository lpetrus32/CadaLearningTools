from django.shortcuts import render
from django.core.cache import cache

from babel import Locale
from googletrans import Translator, LANGUAGES

import asyncio


def get_languages():

    # Cherche d'abord la liste dans le cache
    languages = cache.get("googletrans_languages")

    if languages is not None:
        return languages

    # Si elle n'existe pas encore, on la construit
    french_locale = Locale("fr")
    languages = []

    for code, english_name in LANGUAGES.items():

        # Nom de la langue en français
        french_name = french_locale.languages.get(
            code,
            english_name
        )

        # Nom de la langue dans sa propre langue
        try:
            native_locale = Locale(code)

            native_name = native_locale.languages.get(
                code,
                english_name
            )

        except Exception:
            native_name = english_name

        languages.append({
            "code": code,
            "name": french_name,
            "native_name": native_name,
            "search": f"{french_name} {native_name}",
        })

    # Tri alphabétique français
    languages.sort(
        key=lambda language: language["name"]
    )

    # Stockage dans le cache
    cache.set(
        "googletrans_languages",
        languages,
        timeout=None
    )

    return languages


async def translate_text_async(
    text,
    language_codes,
    language_names
):
    translations = []

    async with Translator() as translator:

        for code in language_codes:

            language_name = language_names.get(
                code,
                code
            )

            try:
                print(code, language_name)
                result = await translator.translate(
                    text,
                    dest=code
                )
                
                translations.append({
                    "code": code,
                    "language": language_name,
                    "text": result.text,
                })

            except Exception as error:

                translations.append({
                    "code": code,
                    "language": language_name,
                    "text": f"Erreur de traduction : {error}",
                })

    return translations


def translate_text(text, language_codes):

    languages = get_languages()

    language_names = {
        language["code"]: language["name"]
        for language in languages
    }

    return asyncio.run(
        translate_text_async(
            text,
            language_codes,
            language_names
        )
    )


def home(request):

    languages = get_languages()

    text = ""
    selected_languages = []
    translations = []

    if request.method == "POST":

        text = request.POST.get(
            "text",
            ""
        ).strip()

        selected_languages = request.POST.getlist(
            "languages"
        )

        if text and selected_languages:

            translations = translate_text(
                text,
                selected_languages
            )

    context = {
        "LANGUAGES": languages,
        "TEXT": text,
        "SELECTED_LANG": selected_languages,
        "TRANSLATIONS": translations,
    }

    return render(
        request,
        "Traductor/home.html",
        context
    )