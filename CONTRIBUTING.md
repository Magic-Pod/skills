# Contributing

This repository is public. Not only the files, but also commit messages, pull request titles and descriptions, and branch names can be seen by anyone.

## Do not include

- Customer company names, contact names, or anything customers told us
- Specific names, URLs, or screens of the sites or apps we tested (write skill examples in a general way that fits any app)
- Internal links (internal GitHub repositories, Slack, Notion, HubSpot, Google Drive, Productboard, etc.)
- Internal Slack channel names, internal terms, or internal project names
- API keys, tokens, or passwords
- Personal default values, such as your own MagicPod organization or project name

## Naming rules

- Put each skill in `skills/<skill-name>/SKILL.md`
- Start skill names with `magicpod-`, and use only lowercase letters, numbers, and hyphens (for example, `magicpod-smoke`)
- Make `name` in SKILL.md the same as the folder name

These rules are checked automatically (`scripts/check-naming.sh`).

## Language

- Write `description` in SKILL.md in both English and Japanese: English first, then ` / `, then Japanese. The description decides when the skill is used, so include example requests in both languages.
- Write the body of SKILL.md in Japanese.
- Write README in both English and Japanese, and CONTRIBUTING in English.

The README and description rules are checked automatically (`scripts/check-docs.py`). The check only looks at the form (English before ` / `, Japanese after it), not at the meaning.

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md` (see "Naming rules" and "Language")
2. Add the skill to the skills table in both the English and Japanese sections of README
3. Bump `version` in `.claude-plugin/plugin.json`

## How to make a change

1. Create a branch and make your change
2. Run `bash scripts/validate.sh` locally and make sure all checks pass
3. Open a pull request (do not include anything from "Do not include" in the title or description)
4. Merge after the `validate` check in GitHub Actions passes

## Automated checks (`validate`)

These checks run when a pull request is opened and when `main` is updated:

1. Agent Skills spec (`name` / `description` in SKILL.md, etc.)
2. Claude Code plugin definitions (`.claude-plugin/plugin.json` / `marketplace.json`)
3. Discoverability (skills can still be found and installed after folders are moved)
4. Naming rules (`scripts/check-naming.sh`; see "Naming rules" above)
5. README and description (`scripts/check-docs.py`; every skill is in both README tables, and each description is written as "English / Japanese")
6. Version (`scripts/check-version.sh`; if `skills/` or `.claude-plugin/` changed, `version` in plugin.json must be higher than on `main`. Without this, users who already installed the plugin do not get the update)
7. Internal information (`scripts/check-internal-info.sh`; also checks the pull request title and description)

Check 7 only looks for fixed patterns. It cannot find company names or customer stories, so please also review your change yourself before opening a pull request.

## Release

1. Bump `version` in `.claude-plugin/plugin.json` (use `x.y.z`; check 6 fails if you forget)
2. After merging into `main`, create a GitHub Release
