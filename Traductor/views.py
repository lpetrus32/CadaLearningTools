
from babel import Locale
from deep_translator import GoogleTranslator
import time

from django.shortcuts import render
from django.core.cache import cache
from django.utils.text import slugify



def get_languages():
    """Retourne la liste des langues avec nom FR et nom natif, en cache."""
    languages = cache.get("deep_translator_languages")
    if languages is not None:
        return languages

    # dict {nom_anglais: code} fourni par deep_translator
    supported = GoogleTranslator().get_supported_languages(as_dict=True)

    french_locale = Locale("fr")
    languages = []

    for english_name, code in supported.items():
        french_name = french_locale.languages.get(code, english_name)

        try:
            native_locale = Locale.parse(code, sep='-')
            native_name = native_locale.languages.get(code, english_name)
        except Exception:
            native_name = english_name

        languages.append({
            "code": code,
            "name": french_name,
            "native_name": native_name,
            "search": f"{french_name} {native_name}",
        })

    languages.sort(key=lambda language: language["name"])
    cache.set("deep_translator_languages", languages, timeout=None)

    return languages


def translate_one(text, code, source="fr", retries=2, delay=1):
    cache_key = slugify(f"translation_{source}_{code}_{text}")
    cached_result = cache.get(cache_key)
   
    if cached_result is not None: 
        return cached_result

    last_error = None

    for attempt in range(retries + 1):
        try:
            result = GoogleTranslator(source=source, target=code).translate(text)
            cache.set(cache_key, result, timeout=None)
            return result
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(delay)

    raise last_error


def translate_text(text, language_codes, source="fr"):
    if not text or not language_codes:
        return []

    languages = get_languages()
    language_names = {
        language["code"]: language["name"]
        for language in languages
        if language["code"] in language_codes
    }

    unique_codes = list(dict.fromkeys(
        code for code in language_codes
    ))

    if not unique_codes:
        return []

    translations = []
    for code in unique_codes:
        language_name = language_names.get(code, code)

        try:
            result_text = translate_one(
                text,
                code,
                source=source,
                retries=4,
                delay=1
            )
            is_erreur = False
        except Exception:
            result_text = f"Erreur de traduction"
            is_erreur = True
           
        translations.append({
            "code": code,
            "language": language_name,
            "text": result_text,
            "is_erreur": is_erreur
        })

    return translations


def home(request):

    languages = get_languages()

    text = ""
    selected_languages = []
    translations = []

    if request.method == "POST":

        text = request.POST.get(
            "text",
            "").strip()

        selected_languages = request.POST.getlist(
            "languages") 

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