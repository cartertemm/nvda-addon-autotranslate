#!/usr/bin/env python3
import os
import sys
import subprocess
import configparser
import gettext
import glob

import llm


DOC_TRANSLATION_PROMPT = """Please translate the following documentation.
Do not include any extra commentary; output only the translated text.
Do not translate the name of the product."""

MANIFEST_TRANSLATION_PROMPT = """Please translate the following manifests INI file text into the provided language.
Do not include any extra commentary; output only the translated text.
Ensure the output preserves the names of the keys and conforms to the INI format without any sections.
Do not translate the keys in the provided list of exclusions if they exist."""

POT_TO_PO_PROMPT = """Please convert the following gettext POT file into a complete PO file for the specified language.
Retain the structure, comments, and msgid entries exactly as provided.
For each translated entry, preserve its corresponding context and reference lines.
For any msgid that does not have a translation provided, populate the msgstr.
Ensure that the header is updated appropriately, including setting the "Language:" field to {language} and the Last-Translator field to {Last-Translator}.
Output only the resulting PO file text with no additional commentary."""


def get_author_info_from_git():
	"""Get stored Git user name and email.

	Returns:
		tuple: (name, email) from git configuration.
	"""
	try:
		name = subprocess.check_output("git config user.name").decode()
		email = subprocess.check_output("git config user.email").decode()
	except (FileNotFoundError, subprocess.CalledProcessError):
		print(
			f"Error obtaining author information from git. Either git is not installed, or the user.name and user.email configuration options have not been defined."
		)
		sys.exit(1)
	return name.strip(), email.strip()


def get_llm(name):
	"""Get the LLM model instance.
	Name can be partial, like GPT-4o."""
	return llm.get_model(name)


def prompt_ai(model, text, fenced=True):
	"""Prompt the AI model with the given text.

	Args:
		model: The language model instance. Call `get_llm()` to get this.
		text (str): The prompt text to send to the model.
		fenced (bool): Whether to extract a fenced code block from the response.

	Returns:
		str: The response from the AI model.
	"""
	response = model.prompt(text).text()
	if fenced:
		cb = llm.utils.extract_fenced_code_block(response)
		if cb:
			return cb
		else:
			print(f"Warning: failed to extract fenced code block. Continuing...")
	return response


def validate_languages(languages):
	"""Validate and process a list of languages (either str or sequence), returning the processed language codes."""
	newlangs = []
	for lang in languages:
		lang = gettext._expand_lang(lang)
		if len(lang) < 2:
			print(f"Warning: Unrecognized language: {lang}.")
			if not input("Would you like to continue? (y/n)").lower().startswith("y"):
				sys.exit(1)
		newlangs.append(lang[1])
	return newlangs


def translate_docs(readme_path, addon_dir, model, languages):
	with open(readme_path, "r", encoding="utf-8") as f:
		content = f.read()
	for lang in languages:
		prompt_text = f"{DOC_TRANSLATION_PROMPT}\nLanguage: {lang}\n\n{content}"
		translated = prompt_ai(model, prompt_text, fenced=True)
		output_dir = os.path.join(addon_dir, "doc", lang)
		os.makedirs(output_dir, exist_ok=True)
		out_file = os.path.join(output_dir, "readme.md")
		with open(out_file, "w", encoding="utf-8") as outf:
			outf.write(translated)
		print(f"Wrote {len(translated)} characters to {out_file}")


def translate_manifests(addon_dir, model, languages):
	protected_keys = {
		"name",
		"author",
		"url",
		"version",
		"docFileName",
		"minimumNVDAVersion",
		"lastTestedNVDAVersion",
		"updateChannel",
	}  # never alter these keys" values
	with open(os.path.join(addon_dir, "manifest.ini"), "r", encoding="utf-8") as f:
		manifest_ini = f.read()
	for lang in languages:
		manifest_dir = os.path.join(addon_dir, "locale", lang)
		manifest_file = os.path.join(manifest_dir, "manifest.ini")
		os.makedirs(manifest_dir, exist_ok=True)
		prompt_text = f"{MANIFEST_TRANSLATION_PROMPT}\nLanguage: {lang}\nexclusions: {', '.join(protected_keys)}\n\n{manifest_ini}"
		translated_manifest = prompt_ai(model, prompt_text, fenced=False)
		with open(manifest_file, "w", encoding="utf-8") as f:
			f.write(translated_manifest)
		print(f"Wrote {len(translated_manifest)} characters to {manifest_file}")


def translate_messages(author, addon_dir, pot_file, model, languages):
	with open(pot_file, "r", encoding="utf-8") as f:
		pot_content = f.read()
	for lang in languages:
		po_file = os.path.join(addon_dir, "locale", lang, "LC_MESSAGES", "nvda.po")
		os.makedirs(os.path.dirname(po_file), exist_ok=True)
		prompt_text = f"{POT_TO_PO_PROMPT.replace('{language}', lang).replace('{Last-Translator}', author)}\n\n{pot_content}"
		translated_po = prompt_ai(model, prompt_text, fenced=True)
		with open(po_file, "w", encoding="utf-8") as f:
			f.write(translated_po)
		print(f"Wrote {len(translated_po)} characters to {po_file}")


def parse_args():
	import argparse

	parser = argparse.ArgumentParser(description="NVDA Add-on AutoTranslate")
	parser.add_argument(
		"-i", "--input", default="addon", help="Input directory containing the addon"
	)
	parser.add_argument(
		"-l",
		"--languages",
		default="es",
		help="Languages to translate to, separated by spaces",
	)
	parser.add_argument("-p", "--pot", help="Path to the pot file")
	parser.add_argument(
		"-r",
		"--readme",
		help="Path to the readme file with the add-ons documentation, defaults to readme.md.",
		default="readme.md",
	)
	parser.add_argument(
		"--author-name",
		help="Author name. If not provided, defaults to the user.name setting from the git configuration.",
		default=None,
	)
	parser.add_argument(
		"--author-email",
		help="Author email. If not provided, defaults to the user.email setting from the git configuration.",
		default=None,
	)
	parser.add_argument(
		"-m",
		"--model",
		help="The full or short name of the large language model to use, e.g. 4o for GPT-4O. Defaults to the one used by the llm tool.",
		default=None,
	)
	return parser.parse_args()


def run(
	addon_dir,
	languages,
	readme="readme.md",
	pot_file=None,
	author_name=None,
	author_email=None,
	model_name=None,
):
	if author_name is None or author_email is None:
		git_name, git_email = get_author_info_from_git()
		if author_name is None:
			author_name = git_name
		if author_email is None:
			author_email = git_email
	author = f"{author_name} <{author_email}>"
	if not os.path.isdir(addon_dir):
		raise ValueError(
			f"Error: Could not find {addon_dir} directory. Please provide a valid path to the add-on."
		)
	manifest_file = os.path.join(addon_dir, "manifest.ini")
	if not os.path.isfile(manifest_file):
		raise ValueError(
			f"Error: Could not find manifest.ini in the {addon_dir} directory."
		)
	with open(manifest_file, "r", encoding="utf-8") as f:
		contents = f.read()
	contents = "[DEFAULT]\n" + contents  # configparser likes to have a section
	config = configparser.ConfigParser()
	config.read_string(contents)
	if "name" not in config["DEFAULT"]:
		raise ValueError("Error: 'name' not found in manifest.ini")
	addon_name = config["DEFAULT"]["name"]
	if pot_file is None:
		pot_file = addon_name + ".pot"
	if not os.path.isfile(pot_file):
		raise FileNotFoundError(
			f"Error: The pot file {pot_file} could not be found. Please run `scons pot` to generate one."
		)
	if not os.path.isfile(readme):
		raise FileNotFoundError(f"Error: The readme file {readme} does not exist.")
	langs = languages if isinstance(languages, list) else languages.split()
	pretty_langs = validate_languages(langs)
	model = get_llm(model_name)
	print(f"Translating {addon_name} to language(s): {', '.join(pretty_langs)} using {model.model_id}")
	print("Documentation...")
	translate_docs(readme, addon_dir, model, langs)
	print("Manifests...")
	translate_manifests(addon_dir, model, langs)
	print("Messages...")
	translate_messages(author, addon_dir, pot_file, model, langs)


if __name__ == "__main__":
	args = parse_args()
	run(
		args.input,
		args.languages,
		args.readme,
		pot_file=args.pot,
		author_name=args.author_name,
		author_email=args.author_email,
		model_name=args.model,
	)
