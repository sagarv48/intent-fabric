# Release Process

This repository uses lightweight semantic versioning tags with a changelog-first workflow.

## 1. Prepare release notes

1. Update `CHANGELOG.md`
2. Move entries from `Unreleased` to a new version section
3. Keep notes scoped to planning/policy/simulation behavior changes

## 2. Create and push tag

```bash
git tag v0.1.1
git push origin v0.1.1
```

## 3. Publish release on GitHub

- Title: version tag (for example `v0.1.1`)
- Description: corresponding `CHANGELOG.md` section
- Mark as pre-release when needed

## 4. Post-release checklist

- Confirm CI green on default branch
- Confirm changelog includes all user-visible changes
- Confirm no runtime connector code was introduced in Phase 2
