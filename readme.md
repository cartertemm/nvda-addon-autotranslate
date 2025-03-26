# NVDA Add-on AutoTranslate

Welcome to NVDA Add-on AutoTranslate!
This tool is an experiment designed to automate the process of translating NVDA (NonVisual Desktop Access) add-ons into different languages using AI-powered large language models.
If you've ever tried to localize software, you know it can be a time-consuming task.
The NVDA community is incredibly generous, yet the vast majority of addons are only available in a few languages. I believe two things to be true:

* An error-prone translation is better than no translation at all.
* It would be better if the precious time of volunteers was spent reviewing and modifying existing language files, instead of recreating them.

With AutoTranslate you get to focus on development while letting AI handle most of the boring stuff, then step aside while a human perfects it.

## Features

- Automatically translates readme documentation, manifest.ini, and message files (.pot) into different languages.
- Choose from a massive collection of models from OpenAI, Anthropic, MistralAI, Google, Command R, Grok, DeepSeek, Ollama, and many more. Under the hood we use the amazing [LLM utility](https://llm.datasette.io/), so the world is your oyster.
- Adapts to different NVDA add-ons with minimal setup.
- Can be used as both a CLI application and Python module.

## Installation

1. Clone the repository:
```
git clone https://github.com/cartertemm/nvda-addon-autotranslate.git
cd nvda-addon-autotranslate
```

2. Install LLM (if not already available):
```
pip install llm
```

3. Configure LLM. By default, only OpenAI models are supported. You can change this by running `llm install` on any of the many [LLM plugins](https://llm.datasette.io/en/stable/plugins/directory.html#plugin-directory). For example, to work with the Claude family:
```
llm install llm-anthropic
```

4. Specify an API key. The easiest way is to do so through LLM directly:
```llm keys set openai``` or ```llm keys set anthropic```

5. LLM will default to gpt-4o-mini. You can override this when you invoke addon-autotranslate with the `-m` parameter (more on this below). Or to save a little typing, just do `llm models default model_name`.

6. Run `xgettext` or `scons pot` (if using the addon template). Otherwise, do what you do to generate a .pot file.

## Usage

The most basic invocation is

```bash
python addon-autotranslate.py -l es
```

Which will look for a folder called `addon` and file called `readme.md` in the current directory, parse the manifest.ini, find the .pot file, and translate to Spanish.

If your add-on files (doc, locale, manifest.ini, etc) are somewhere else, specify a path with the `-i` option.

PO files need an author so that project maintainers know who to get a hold of when they want to release updates. By default we pull the `user.name` and `user.email` values from your local git configuration. If you don't want to be liable when the AI makes an embarrissing mistake, pass `--author-name` and `--author-email`.

You can provide multiple languages to the `-l` parameter, like `-l "de es fr"`, or even specify a locale such as `"es-mx"`.

To change the model, pass something like `-m claude-3.5-sonnet`.

`-p` and `-r` change the paths to the pot file and readme, respectively.

## Contributing

Truthfully, I started hacking on this during a lunch break and released it upon request from a fellow add-on developer. I know it's not perfect (not even close). Together, maybe we can fix that.
I welcome contributions! If you find a bug or have a feature request, open an issue and we can chat about it. If something is really broken and is straightforward enough to fix, feel free to submit a PR.
