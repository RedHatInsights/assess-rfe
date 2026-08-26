# assess-rfe

Claude Code plugin for assessing RFEs against quality criteria using a structured rubric.

## Skills

- **assess-rfe** — Apply a status-aware RFE rubric in single-issue or bulk mode: Misclassified, WHAT, WHY, and Strategic in Backlog; HOW and Well-Scoped in Refinement
- **export-rubric** — Export the scoring rubric to a standalone markdown file

## Installation

```bash
claude plugin marketplace add opendatahub-io/skills-registry
/plugin install assess-rfe@opendatahub-skills
```

## Usage

```
/assess-rfe RHAIRFE-1234        # assess a single RFE
/assess-rfe RHAIRFE-*           # bulk assess all RFEs in the project
/export-rubric                  # export the rubric to artifacts/rfe-rubric.md
```

## License

Apache-2.0
