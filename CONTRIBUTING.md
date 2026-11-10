# Contributing

This repository is public. Not only the files, but also commit messages, pull request titles and descriptions, and branch names can be seen by anyone.

## Do not include

- Customer company names, contact names, or anything customers told us
- Specific names, URLs, or screens of the sites or apps we tested (write skill examples in a general way that fits any app)
- Internal links (internal GitHub repositories, Slack, Notion, HubSpot, Google Drive, Productboard, etc.)
- Internal Slack channel names, internal terms, or internal project names
- API keys, tokens, or passwords
- Personal default values, such as your own MagicPod organization or project name

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
4. Internal information (`scripts/check-internal-info.sh`; also checks the pull request title and description)

Check 4 only looks for fixed patterns. It cannot find company names or customer stories, so please also review your change yourself before opening a pull request.

## Release

1. Bump `version` in `.claude-plugin/plugin.json`
2. After merging into `main`, create a GitHub Release
