from django.shortcuts import render
import pycountry

from babel import Locale

import asyncio
from googletrans import Translator


def get_languages():
    french_locale = Locale("fr")
    languages = []

    for language in pycountry.languages:

        if not hasattr(language, "alpha_2"):
            continue

        code = language.alpha_2

        try:
            french_name = french_locale.languages.get(
                code,
                language.name
            )
        except Exception:
            french_name = language.name

        try:
            native_locale = Locale(code)

            native_name = native_locale.languages.get(
                code,
                language.name
            )

        except Exception:
            native_name = language.name

        languages.append({
            "code": code,
            "name": french_name,
            "native_name": native_name,
            "search": f"{french_name} {native_name}",
        })

    languages.sort(
        key=lambda language: language["name"]
    )

    return languages



async def translate_text_async(text, language_codes, language_names):
    translations = []

    async with Translator() as translator:

        for code in language_codes:

            language_name = language_names.get(code, code)

            try:
                result = await translator.translate(
                    text,
                    dest=code,
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
            language_names,
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