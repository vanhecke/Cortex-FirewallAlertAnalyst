# Agentix agent spec

What a pack must contain for an Agentix agent to validate and to work on a tenant.

Sources: demisto-sdk v1.39.6 (HEAD `baa008469`) - its schemas, strict objects, parsers,
preparers and AG/GR validators, plus its git history - and live deploys of
`FirewallAlertAnalyst` to Cortex XSIAM tenants. File paths below are relative to a
demisto-sdk checkout.

Section 11 was re-checked against `a6e095a90` (2026-09-18) and rewritten. On 2026-11-04 the
whole spec was re-checked against **demisto-sdk 1.39.13** and a live deploy to a **Cortex
XSIAM 4.0** tenant (server 8.16.0); see section 0 for what changed.

`*` marks anything not verified end to end.

---

## 0. XSIAM 4.0 and demisto-sdk 1.39.13

XSIAM 4.0 (server 8.16.0, November 2026, alongside Agentix 1.5) and demisto-sdk 1.39.13
(2026-10-20). Verified by deploying this pack to a 4.0 tenant on 2026-11-04, then
uninstalling it.

| Change | Where | Section |
| --- | --- | --- |
| `Collections/` is now `Knowledge/`, and the agent field `collectionids` is now `knowledgeids`. The server field is unchanged (`systemknowledgecollectionids`) | SDK 1.39.13 | 1, 2, 4, 11 |
| Agents can declare MCP servers natively: `mcps: [{server_url: ...}]`. Stored on 4.0 | SDK 1.39.9, 4.0 | 4, 16 |
| Actions can be long-running: `islongrunning`, `longrunningtimeoutseconds`. Stored on 4.0 | SDK 1.39.9, 4.0 | 5 |
| `display` on an agent was never in the schema; ST110 rejects it | SDK | 4 |
| ST110 (strict schema) must be selected, or renamed and unknown fields pass silently | SDK | 13 |
| `zip-packs` builds for the xsoar marketplace and drops every agent item; build with `prepare-content -mp platform` | SDK | 13 |
| Palo Alto ships 10 managed knowledge collections. A pack agent can bind one by id (`cortex-platform-docs`); stored on 4.0 | 4.0 | 11d |
| 47 `_builtin_` action handlers (6 on 8.15), stored as `type: command`, not `internal` | 4.0 | 9 |
| Knowledge-source binding is unchanged: `userAgentIds` on the source fills `userKnowledgeSourceIds` on the agent | 4.0 | 11b |
| Uninstall can drop the first request, and leaves pack knowledge collections behind as undeletable system items | 4.0 | 14 |

Unchanged on 4.0, re-verified: all seven actions install live (prompt and playbook
included), prompt `modelTier` and `systemInstruction` are kept, `systemInstructions` still
reads back encrypted, and `/skills` still has no endpoint.

---

## 1. Content types

| Type | Pack dir | Server name | Uploaded |
| --- | --- | --- | --- |
| AgentixAgent | `AgentixAgents/` | `agentixagent` | yes |
| AgentixAction | `AgentixActions/` | `agentixaction` | yes |
| AgentixActionTest | `AgentixActions/` | - | **no** (`CONTENT_TYPES_EXCLUDED_FROM_UPLOAD`) |
| AgentixSkill | `AgentixSkills/` | `agentixskill` | yes |
| Knowledge | `Knowledge/` | `agentixknowledgecollection` | yes (name/description only, see 11) |
| Script | `Scripts/` | `automation` | yes |

Release-note headers: `Agents`, `Actions`, `Skills`, `Knowledge`.

demisto-sdk 1.39.12 and earlier call the Knowledge type `Collection`, in `Collections/`,
with release-note header `Collections`. A pack written for one side of that rename does
not validate on the other. The server type and stored object are the same either way.

## 2. File layout

```
Packs/<Pack>/
  pack_metadata.json
  AgentixAgents/<AgentId>/<AgentId>.yml
                          <AgentId>_systeminstructions.md   MANDATORY (AG110)
                          <AgentId>_test.yml                optional, never parsed (1.39.13)
  AgentixActions/<ActionId>/<ActionId>.yml
                            <ActionId>_test.yml             MANDATORY (AG118)
  AgentixSkills/<SkillId>/<SkillId>.yml
                          <SkillId>_skill.md                MANDATORY (AG111)
  Knowledge/<KnowledgeId>/<KnowledgeId>.yml                 (Collections/ before 1.39.13)
  Scripts/<ScriptId>/<ScriptId>.yml [+ <ScriptId>.py]
```

Directory name == file stem == `commonfields.id`. The sidecar `.md` suffix is derived from
the **folder** name, not the yml id.

Markdown sidecars are merged into the yml at prepare-upload
(`prepare_content/agentix_markdown_unifier.py`):

- `<folder>_skill.md` -> skill `content`
- `<folder>_systeminstructions.md` -> agent `systeminstructions`

Author the `.md`; leave the yml field as `""`.

## 3. Naming

Enforced:

- Action `name`: `^[a-zA-Z]\w*$` (AG106). No spaces, no hyphens.
- Action `display`: `^[A-Za-z][A-Za-z0-9_\- ]*$` (AG107).
- All Action / Skill / Collection text: ASCII only (AG114).

Convention used here (not enforced): id ends with a token naming the type -
`-agent`, `-skill`, `Action`, `Script`, `Prompt`, `Collection`. Agents and skills
kebab-case, everything else PascalCase. Set action `name` == `commonfields.id`; this makes
the skill token rewrite in 10 an identity transform.

## 4. AgentixAgent

Schema `common/schemas/agentixagent.yml`.

| Field | Req | Notes |
| --- | --- | --- |
| `commonfields.id` / `.version` | yes | `version: -1` |
| `name`, `description` | yes | |
| `color` | yes | `^#[0-9a-fA-F]{6}$` (AG108) |
| `visibility` | yes | `public` \| `private` (AG104) |
| `systeminstructions` | no | `""`; filled from the `.md`. Max 65535 **bytes** (AG109) |
| `actionids` | no | AgentixAction ids |
| `skillids` | no | AgentixSkill ids |
| `knowledgeids` | no | Knowledge ids; may name a Palo Alto managed collection (11d). `collectionids` before 1.39.13 |
| `mcps` | no | list of `{server_url: <url>}` (1.39.9+). See 16 |
| `builtinactions` | no | platform capability names, see 9 |
| `conversationstarters` | no | list of strings |
| `autoenablenewactions` | no | bool |
| `roles`, `sharedwithroles` | no | RBAC |
| `category`, `tags` | no | AG102 constrains `category` |
| `marketplaces` | no | must be `[platform]` (AG101) |
| `supportedModules` | no | `[agentix]` |
| `supportedFeatures`, `excludefromtightlycoupled` | no | 1.39.10+; not exercised here |

There is no `display` field on an agent. It is not in the schema, ST110 rejects it, and the
server stores only `name`. (Actions do have `display`.) Every field above was read back
from a 4.0 tenant after upload, `mcps` and both `knowledgeids` entries included.

Total agent context <= 200000 chars (GR116): agent name + description + system
instructions + conversation starters, plus name + description of every registered action,
skill and collection, plus action args/outputs schemas. Skill **bodies** are excluded.

## 5. AgentixAction

Schema `common/schemas/agentixaction.yml`.

| Field | Req | Notes |
| --- | --- | --- |
| `commonfields.id` / `.version` | yes | |
| `name` | no (schema) | but AG106 applies; always set it |
| `display` | no (schema) | AG107 applies |
| `description` | no (schema) | the router key; always set it |
| `args` | no | <= 10 (AG117); no duplicate names (AG103) |
| `outputs` | no | |
| `underlyingcontentitem` | **yes** | see 6 |
| `requiresuserapproval` | no | bool |
| `fewshots` | no | **list of strings**; not counted by AG112 |
| `internal` | no | bool, hides from UI/API - unrelated to `underlyingcontentitem.type: internal` |
| `islongrunning` | no | bool (1.39.9+). Stored as `isLongRunning` |
| `longrunningtimeoutseconds` | no | int (1.39.9+). Stored as `longRunningTimeoutSeconds` |
| `marketplaces` | no | `[platform]` (AG101) |

Long-running actions are new in XSIAM 4.0. The tenant's only built-in one is
`CortexIngestLogs` at 3600 seconds. `BlockIpAction` here sets `true` / 1800, because its
playbook waits on a human verification step. Both fields read back as set. What the
runtime does differently for a long-running action is undocumented.*

`args[]`: `name`, `description`, `type` required; optional `required`, `defaultvalue`
(string), `hidden`, `disabled`, `isgeneratable`, `underlyingargname`.

`isgeneratable` is a **marker, not a constraint.** The SDK defines no semantics for it at
all - it is `isgeneratable: bool = False` in the schema and both models, with no
validator, no docstring and no prose anywhere. Tested live: an argument marked
`isgeneratable: false` was still filled in by the agent, unprompted, with a plausible
value. So `false` does not prevent the model from generating a value and is better read
as "unmarked" than as "forbidden". PANW marks 20 of 803 shipped args `true`, and every one
is free prose the model authors from nothing - mail subject/body, war-room entry content,
notification message, new rule names and descriptions. Identifiers, enums and pagination
(`limit`, `case_id`, `status`, `severity`, `assignee`) are left `false`.

To actually constrain an argument, validate it in the backing script and return an error.
Arg descriptions and skill text steer; only code enforces.
Whether the flag has any runtime effect at all, or is purely a UI affordance, is
unknown.*

`outputs[]`: `name`, `description`, `type` required; optional `disabled`,
`underlyingoutputcontextpath`.

Types are a closed list (AG105):

- args: `unknown`, `string`, `number`, `date`, `boolean`
- outputs: the same plus `json`

Budget: name + description + args schema + outputs schema <= 4000 chars (AG112).

## 6. `underlyingcontentitem`

`id`, `name`, `type`, `version` required by schema; `command` optional by schema.

| `type` | `id`/`name` | `command` | Graph dependency |
| --- | --- | --- | --- |
| `command` | integration id, or `_any_` | required | `USES_COMMAND_OR_SCRIPT`, mandatory |
| `script` | Script id | - | `USES_BY_ID` -> Script, mandatory |
| `playbook` | Playbook id | - | `USES_BY_ID` -> Playbook, mandatory |
| `prompt` | Script id with `isllm: true` | - | `USES_BY_ID` -> Script, mandatory |
| `internal` | rewritten to `_builtin_` by server | required by server | none |
| `MCP Tool` | `<Integration>-<Instance>-<tool>` | empty | SERVER-ONLY, see 16 |

`MCP Tool` exists on the server but NOT in the SDK. GR110 rejects any type outside
{command, script, playbook, internal, prompt} as "currently unsupported in Agentix", so a
pack cannot declare one.

`_any_` and `_builtin_` are skipped by GR110. `_any_` binds to whichever enabled instance
provides the command.

For `playbook`, `id` and `name` are the playbook's name and `command` is empty. Arguments
map to playbook INPUT keys via `underlyingargname` (case-sensitive: `IP`, `RuleName`).
Note a playbook-backed action cannot be authored in the web UI - the action editor offers
commands and scripts only - so it has to come from a pack. The tenant ships 5 of them
(all PAN-OS) out of 130 actions.

**Do not author `type: internal`.** It does not mean "an action with no backing item"; it
means "a platform builtin named by `command`", and the builtin cannot be authored in a
pack. Nothing catches a wrong name: the schema makes `command` optional, GR110 `continue`s
on `internal` before resolving, and tenant `live` is derived from `state.errorCode` being
empty - since nothing resolves, no error is ever raised and a dead action reports healthy.
The server rewrites `id`/`name` to `_builtin_` and keeps only `command`. Verified live.

## 7. AgentixActionTest

`<ActionId>_test.yml` beside `<ActionId>.yml`. Mandatory (AG118). Never uploaded.

```yaml
tests:
  - name: <str>
    prompt: <str>
    agent_id: <AgentixAgent id>     # mandatory graph edge
    expected_outcomes:
      - evaluation_mode: any_of | sequence
        actions:
          - action_name: <action NAME, not id>
            arguments: {<arg>: <value>}
        expected_output: <str>
        expected_error: <str>
fixtures: []
```

Model: `content_graph/strict_objects/agentix_action_test.py`. `action_name` resolves
against the action's `name` (changed in #5313).

## 8. AgentixSkill

Schema `common/schemas/agentixskill.yml`. Required: `commonfields.id`/`.version`, `name`,
`description`. Optional: `content` (`""`, filled from `_skill.md`), `tags`, `category`,
`disabled`, `internal`, `marketplaces`, `supportedModules`.

- `description` must be 10-200 words (AG115). It is the router matching key.
- name + description + skill body <= 8000 chars (AG112).
- An agent registering a skill must list every action the skill references in its own
  `actionids` (AG116).

## 9. Builtin actions

Two distinct mechanisms, easily confused:

1. Agent `builtinactions`: capability names on the agent. Seen live: `InvokeLLM`,
   `CortexRunXQLQuery`, `HelpCenter`. `InvokeLLM` is on 12 of 14 tenant agents; a
   prompt-backed action appears to need it.*
2. Action `underlyingcontentitem` with `id`/`name: _builtin_`: binds to a platform
   handler named in `command`, lowerCamelCase. The six on the tenant:
   `runXQLQuery`, `setCase`, `getSystemUsers`, `getSystemGroups`, `enrichIndicators`,
   `extractIndicators`. No builtin READS a case; use `core-get-cases` via `_any_`.

You cannot add a builtin handler from a pack.

**XSIAM 4.0.** The PANW agents carry only `InvokeLLM` (11 of 12). A pack agent's
`CortexRunXQLQuery` was still accepted and stored. The `_builtin_` handlers grew from 6 to
47, and the server now stores them as `type: command` with `id`/`name: _builtin_`, not as
`type: internal`. Among the new ones: `listIssues`, `updateIssue`, `createWarRoomEntry`,
`getEndpoints`, `isolateEndpoint`, `runPlaybook`, `runScriptAgentix`, `getAgentixAgents`
and `createAgentixAgent`. `listIssues` reads issues; still no builtin reads a case. Agents
built in the UI bind these heavily (up to 23 on one agent). A pack agent can list the
action ids in `actionids` the same way as the MCP ids in 16.* The ids are tenant-side,
so read them from `GET /xsoar/cm/agentix/actions` first.

## 10. Skill action reference tokens

Token: `<action=...>`, regex `<action=([^>]+)>`
(`prepare_content/agentix_markdown_unifier.py:16`).

- Parser registers each unique referenced id as an **optional** `USES_BY_ID` dependency on
  AgentixAction (`parsers/agentix_skill.py`).
- Preparer rewrites `<action=id>` -> `<action=name>` at prepare-upload, resolved through
  the content graph. It substitutes the action's **`name`**, NOT its `display`. The SDK
  test asserts this explicitly (`agentix_skill_action_reference_preparer_test.py`).
  The docstring in `parsers/agentix_skill.py` saying "display name" is wrong.
- Unresolved tokens are left unchanged and logged as a warning, by design.
- `upload` does not populate the graph, so tokens ship as authored. Harmless when
  `name == id`.
- AG116 checks agent `actionids` covers the skill's tokens. GR115 requires a skill release
  note when a referenced action's `name` changes.
- What the runtime does with a resolved token is undocumented.*

There is no prose documentation for this token anywhere in the SDK - no `.md`, no
CHANGELOG entry. The above is read off source and tests.

## 11. Knowledge: knowledge collection vs knowledge source

Two server objects, easily confused. Only one holds text, and the SDK authors only the
other. demisto-sdk 1.39.13 renamed the pack type from Collection to Knowledge; the server
still calls it a knowledge collection.

| | Knowledge collection | Knowledge source |
| --- | --- | --- |
| Pack dir | `Knowledge/<Id>/<Id>.yml` (`Collections/` before 1.39.13) | none |
| Server name | `agentixknowledgecollection` | - |
| List endpoint | `/xsoar/agentix/knowledgecollections` | `/xsoar/cm/agentix/knowledges` |
| Carries text | no (pack-made); not readable (managed, 11d) | yes |
| Agent binding | agent `knowledgeids` (`collectionids` before 1.39.13) | source `userAgentIds` / `systemAgentIds` |
| Authorable in a pack | yes | **no** |

### 11a. Knowledge collection

Schema `common/schemas/knowledge.yml` (`collection.yml` before 1.39.13), unchanged apart
from the name and an optional `supportedFeatures`. Required: `commonfields.id`/`.version`, `name`.
Optional: `description`, `fromversion`, `toversion`, `marketplaces`, `supportedModules`,
`supportedFeatures`, per-marketplace `name:<mp>` / `description:<mp>`.

No content, body, documents, text, files or knowledge field exists, and
`scripts/validate_content_path.py` permits exactly one file per collection folder,
`<Id>.yml`. Contrast `AgentixSkills/`, which also permits `<Id>_skill.md`. There is
nowhere to put a document.

Upload does create the object. `GET /xsoar/agentix/knowledgecollections` returns it with
`status: enabled` and `packID` set. It arrives `sizeInBytes: 0` and stays there.
`description` is metadata, not retrievable content, so an agent whose only knowledge is a
pack collection gets `references: []` from `QueryUserKnowledge`.

Agent binding does work. `knowledgeids` (`collectionids` before 1.39.13) is renamed to
`systemknowledgecollectionids` at prepare-upload
(`prepare_content/agentix_markdown_unifier.py`) and the server keeps it per agent -
verified live on 8.15 and again on 4.0.

1.39.13's `prepare-content` writes the item to `Collections/agentixknowledgecollection-<Id>.yml`
inside the zip, the server's folder name. It then logs `Could not determine content type`
for that path while writing metadata. The item is still in the zip and in
`metadata.json`, and installs. The error is noise.

### 11b. Knowledge source

The object that carries text. API only: no content type, no pack directory, no SDK
support, and tenant-side sources report `packID: ""`.

```
POST   /xsoar/cm/agentix/knowledge          create and update
GET    /xsoar/cm/agentix/knowledges         list
GET    /xsoar/cm/agentix/knowledges/<id>    one
DELETE /xsoar/cm/agentix/knowledges/<id>    delete
```

`DEMISTO_API_KEY` + `XSIAM_AUTH_ID` authenticate all of these on the `api-<tenant>` host;
no browser session is needed. The `/xsoar/cm/` prefix is what the Knowledge Center UI
uses. `/xsoar/agentix/knowledges` answers the reads too. The UI host
(`<tenant>.xdr.<region>...`, no `api-` prefix) rejects API-key auth with a 303 to
`/login`.

Create body, verified live:

```json
{"sourceType": "FILE",
 "name": "worked-alerts.md",
 "contentType": "text/markdown",
 "sharedWithAllAgents": false,
 "userAgentIds": ["firewall-alert-analyst-agent"],
 "systemAgentIds": [],
 "periodicSync": false,
 "sourceDetails": {"datasource": null, "instanceName": null, "args": {}},
 "file": [35, 32, 87, 111, 114, 107, 101, 100]}
```

| Field | Note |
| --- | --- |
| `file` | the document as a JSON array of byte values, ie `list(path.read_bytes())`. Multipart is rejected 415 on every route, so JSON is the only way in |
| `sourceType` | uppercase `FILE`. Lowercase `file`, and `TEXT`/`INLINE`/`URL`/`RAW`/`STRING`, all fail `Invalid SourceType (101803)` |
| `contentType` | lowercase, eg `text/markdown` |
| `name` | the filename, extension included; the server derives the stored object's suffix from it |
| `uri`, `fileHash`, `contentSizeInBytes` | server-controlled. Sending them is silently ignored |

`processingStatus` goes `processing` -> `ready` within a few seconds. On `ready` the object
gains `contentSizeInBytes`, `fileHash` and a bucket `uri`. Omit the `file` bytes and it
settles on `error` with size 0 - that is the only failure signal; the POST still returns
200.

Scoping lives on the source, not on the agent:

| Source field | Agent field it populates |
| --- | --- |
| `userAgentIds` | `userKnowledgeSourceIds` |
| `systemAgentIds` | `systemKnowledgeSourceIds` |
| `sharedWithAllAgents: true` | both, on every agent |

Verified live: `sharedWithAllAgents: false` with one id in `userAgentIds` reached 1 of 15
agents; a source with `true` reached 15 of 15. Both id lists are omitted from GET
responses when empty, which is why they are invisible until you set them.

The UI writes `userAgentIds` and leaves `systemAgentIds` empty for a scoped source. What
the runtime does differently with user versus system knowledge at query time is documented
nowhere.* Only the binding was tested here, not whether a scoped source is actually
retrieved mid-conversation.*

**Unchanged on XSIAM 4.0.** The same create body, posted on 2026-11-04, reached `ready` in
about 3 seconds. The source kept `userAgentIds`, and the agent gained
`userKnowledgeSourceIds: [<source id>]`. On a 4.0 tenant where no source is scoped to any
agent, neither field appears anywhere. That looks like a removal, but it is only the
omit-when-empty rule above.

### 11c. Consequence for packs

An agent that needs real knowledge cannot ship complete. The pack carries the agent and,
optionally, an empty collection handle; the document is a separate API call keyed to the
agent's id.

**Knowledge Center is not supported by demisto-sdk yet.** Confirmed by the SDK developers,
2026-09-28. There is no work-in-progress content type to adopt, and the Collection item is
not a partial implementation of one. Do not expect `upload` to carry a document, and do
not design a pack around it arriving soon.

The source agrees. As of `a6e095a90` (2026-09-18), `git log -S` finds no content field on
Collection anywhere in the repo history, and the only change to the collection files since
the type was added (#5393, 2026-06-11) is the optional `supportedFeatures` list (#5508,
2026-09-17).

Until that changes, shipping an agent with knowledge is two steps: `demisto-sdk upload`
for the pack, then one `POST /xsoar/cm/agentix/knowledge` per document, scoped with
`userAgentIds` to the agent ids the pack just uploaded.

Still true in 1.39.13: the rename to Knowledge added no content field, and
`validate_content_path.py` still allows exactly `Knowledge/<Id>/<Id>.yml`.

### 11d. Managed knowledge collections (XSIAM 4.0)

A 4.0 tenant carries ten knowledge collections that Palo Alto manages: `managed: true`,
`source: agentix`, `isSystem: true`, `fromServerVersion: 8.16.0`, each from a pack named
`AgentixKnowledge_<id>`. Those packs are not in demisto/content, and the tenant's
marketplace endpoints do not show them.

| id | Scope (from its description) |
| --- | --- |
| `cortex-platform-docs` | platform concepts: data model, assets, issues, cases, security graph. Bound to 11 of the 12 built-in agents (not help-center) and to 45 UI-built ones on the test tenant |
| `tac-docs` | TAC guides for XDR/XSIAM endpoint issues and per-integration troubleshooting. Bound to help-center |
| `cwp-knowledge` | Cloud Posture (CWP): inventory, onboarding, scanning. Bound to cloud-posture |
| `aispm-knowledge`, `dspm-knowledge`, `ciem-identity-knowledge` | AI, data and identity security posture |
| `p2xql-docs-md`, `p2xql-docs-docx`, `p2xql-examples` | XQL reference and worked natural-language-to-XQL examples |
| `visualization-knowledge` | json-render visualizations |

Unlike a pack collection, these clearly carry content: the built-in agents answer from
them. But it is not readable over the API. The record holds only a routing description of
300-560 characters, `sizeInBytes` is 0, and every document, file, download and export path
returns 404.

**A pack agent can bind one by id.** `knowledgeids: [cortex-platform-docs]` uploaded
cleanly and read back in `systemKnowledgeCollectionIds`. Nothing checks that the id
resolves, which is the same as for the MCP action ids in 16. Whether the agent actually
retrieves from it mid-conversation is untested.* The ids exist only on 4.0 tenants.

## 12. Backing scripts

Standard Python automation: `type: python`, `subtype: python3`, `dockerimage`, `script`,
`args`, `outputs`, `marketplaces: [platform]`.

Prompt script (`isllm: true`), model `strict_objects/script.py`:

| Rule | Source |
| --- | --- |
| `script` must be absent | strict object |
| `userprompt` mandatory | strict object |
| `model` (legacy, `toversion: 8.12.0`) or `promptConfig` (`fromversion: 8.13.0`) mandatory | strict object |
| `marketplaces: [platform]` mandatory | AG101 |
| if `isllm: false`, all of `model`/`userprompt`/`systemprompt`/`fewshots`/`promptConfig` must be empty | strict object |

`promptConfig`: `temperature`, `maxOutputTokens`, `webSearch`, and `modelTier`
(`Flash`/`Thinking`/`Pro`, SDK 1.39.7 onwards). The server also reads `systemInstruction`,
which the 1.39.9 strict `PromptConfig` does not list. Note `fewshots` on a script is a
**string**; on an action it is a list of strings.

Server rules the SDK does not encode, all verified live. The model and system prompt rules
were checked on 2026-09-28 by reading prompts back from `GET /xsoar/cm/aiTask/<id>` and
running them through a `type: prompt` action:

- Only `promptConfig.modelTier` picks the model. Upload drops a top-level `model` (stored
  `null`), and `promptConfig.model` is stored but ignored at runtime. With no tier the
  prompt runs on the tenant default, with no error.
- Upload drops a top-level `systemprompt`. `promptConfig.systemInstruction` reaches the
  model, although GET returns it as `{MULAN}`.
- Exactly one output required: `'Outputs' attribute must have 1 value (52)`.
- `temperature` is not enforced. `claude-opus-4-8` does not list it in `supportedParams`
  (`claude-sonnet-4-6` does), yet a prompt setting it on the `Pro` tier ran without error.

Re-checked on XSIAM 4.0 through `GET /xsoar/cm/aiTask/<id>`: `modelTier: Pro` is kept,
`systemInstruction` is kept (encrypted), there is one output, and `model` is `null`. The 4.0
docs map the tiers as Flash = Gemini 3.5 Flash, Thinking = Claude Sonnet 4.6 and Pro =
Claude Opus 4.8.

The strict `PromptConfig` still does not list `systemInstruction` in 1.39.13, so ST110
fails a prompt that uses it. Keep the field, because it is the only system prompt the model
reads. Mark ST110 ignorable in the validate config and add a per-file `.pack-ignore` entry
(`ignore=DO104,ST110`), so the exception covers that one file and nothing else.

## 13. Validators

All are errors unless listed as warning. "Graph" = needs a populated content graph, so
`upload`/path-based runs do not execute them.

| Code | Rule | Mandatory | Graph |
| --- | --- | --- | --- |
| AG100 | Agentix items must not go to the content repo | yes | no |
| AG101 | Agentix items + `isllm` scripts: `marketplaces` must be exactly `[platform]` | yes | no |
| AG102 | `category` from the approved list | yes | no |
| AG103 | No duplicate action arg names | yes | no |
| AG104 | Agent `visibility` in `public`/`private` | yes | no |
| AG105 | Arg/output types from the closed list | yes | no |
| AG106 | Action `name` matches `^[a-zA-Z]\w*$` | yes | no |
| AG107 | Action `display` matches `^[A-Za-z][A-Za-z0-9_\- ]*$` | yes | no |
| AG108 | Agent `color` is 6-digit hex with `#` | yes | no |
| AG109 | System instructions <= 65535 bytes | yes | no |
| AG110 | `<AgentId>_systeminstructions.md` exists | yes | no |
| AG111 | `<SkillId>_skill.md` exists | yes | no |
| AG112 | Action <= 4000 chars, skill <= 8000 chars | ignorable | no |
| AG113 | does not exist | - | - |
| AG114 | ASCII only in action/skill/collection text | yes | no |
| AG115 | Skill description 10-200 words | yes | no |
| AG116 | Agent `actionids` covers its skills' referenced actions | yes | yes |
| AG117 | <= 10 args per action | ignorable | no |
| AG118 | `<ActionId>_test.yml` exists | yes | no |
| GR110 | Action's underlying item exists, inputs/outputs match | warning (path) / error (git) | yes |
| GR111 | No duplicate action `display` in the repo | yes | yes |
| GR112 | No duplicate action `name` in the repo | yes | yes |
| GR115 | Action `name` change requires a dependent-skill release note | yes | yes |
| GR116 | Agent total context <= 200000 chars | yes | yes |
| GR117 | No duplicate action `id` (1.39.13) | yes | yes |
| GR118 | No cross-destination dependency (1.39.13)* | yes | yes |
| ST110 | Item matches its strict model: no unknown or renamed fields | yes | no |

AG112 and AG117 are in the SDK's `ignorable_errors`, so `.pack-ignore` can silence them.

**Select ST110.** It is the only rule that notices a field the SDK no longer knows. Under
1.39.13 an agent still carrying `collectionids` passes every AG rule. The 1.39.13 unifier
renames only `knowledgeids`, so the binding would not reach the server under its
server name. An agent with `display` passes the AG rules too. ST110 reports both as
`value_error.extra`.

**Run `validate` with a config or it checks nothing.** The SDK's `default_config.toml`
selects 15 codes and **no** AG or GR rule at all, so an unconfigured run leaves the agent,
actions and skills entirely unchecked. Its `sdk_validation_config.toml` does select them,
but assumes a checkout of demisto/content and aborts on a standalone pack (PA102 fetches
`approved_categories.json`).

This repo therefore ships its own `validation_config.toml` at the root:

```
demisto-sdk validate -i Packs/FirewallAlertAnalyst --config-path validation_config.toml
```

It targets demisto-sdk 1.39.13 and selects AG101, AG103-AG111, AG114, AG115, AG117, AG118
and ST110. Deliberately not selected:
AG100 and AG102 (need a remote fetch), AG112 (character budgets - enable it if your skill
bodies are hand-written), AG116 and all GR rules (need a populated content graph, which
`upload` does not build), and DO104 (raises rather than fails on prompt scripts, which have
no `dockerimage`).

## 14. Other server behaviour

- Content cannot be read back to verify. `systemInstructions` returns encrypted
  (`{MULAN}...`). The agentix endpoints that answer are `/agents`, `/actions`,
  `/knowledgecollections` and `/knowledges`, each also under the `/xsoar/cm/` prefix;
  `/skills` and `/prompts` 303 to `/#/404`. A prompt reads back from
  `/xsoar/cm/aiTask/<id>` instead. A knowledge source exposes `uri`, `fileHash`
  and `contentSizeInBytes` but no readable content field either, so the uploaded document
  is write-only over the API.
- Support varies by tenant version. On an older tenant a prompt-backed action installed
  dead (`underlying content item ... of type [prompt] was not found`) and the agent object
  carried no `skillIds` or `systemKnowledgeCollectionIds` at all.
- Pack uninstall works and is asynchronous:
  `POST /xsoar/contentpacks/installed/delete {"IDs":["<pack>"]}` returns `200 {}`
  immediately; the pack and every item it materialized disappear within ~1 minute.
- Ids are identity. Renaming an id creates a new object and orphans the old one; uninstall
  the pack before re-uploading renamed content.

XSIAM 4.0, verified on 2026-11-04:

- **Build with `prepare-content -mp platform`.** `zip-packs` has no marketplace option and
  builds for `xsoar`, which drops every agent item without a word. `demisto-sdk
  prepare-content -i Packs/<Pack> -o <dir> -mp platform` writes an installable
  `<dir>/<Pack>.zip`. Create `<dir>` first: if it does not exist, the zip is written to
  `<dir>.zip` instead. `demisto-sdk upload -i <Pack>.zip` sends a zip as-is, so an older SDK can
  upload a zip that 1.39.13 built.
- **Detail beats list.** `GET /agents/<id>` and `/actions/<id>` return fields the list
  omits: `systemInstructions` (still `{MULAN}`-encrypted), `builtinActions`, `skillIds` and
  `managed`. Agents built in the web UI store their prompt in `customInstructions`, which
  reads back as plain text. Pack agents use `systemInstructions`.
- **Uninstall is unreliable.** The first `POST /xsoar/contentpacks/installed/delete`,
  sent about 5 minutes after install, returned `200 {}` and did nothing for over 10
  minutes. The same request sent again removed the pack, agent and actions within 50
  seconds. On 2026-11-05 the first request worked, within 40 seconds, so the drop is
  intermittent. Poll `/xsoar/contentpacks/metadata/installed` and resend if needed.
- **Uninstall leaves the knowledge collection behind.** It stays as `isSystem: true` with
  the old `packID`, and `DELETE /xsoar/cm/agentix/knowledgecollections/<id>` refuses with
  `Item is system and cannot be modified (100001)`. A collection from a removed probe pack
  sits on an 8.15 tenant the same way. A later install of a pack carrying the same
  id takes it over again: on 2026-11-05 the leftover took the new `itemVersion` and
  `modified`. Do not put anything in a test collection's description that you would
  not want left on the tenant.

## 15. Reference implementation

`Packs/FirewallAlertAnalyst` exercises `command` (with a named integration and with
`_any_`), `script` and `prompt` underlying types, both `_test.yml` evaluation modes,
`<action=...>` tokens, a collection handle and the full arg/output flag set. See its
README.

## 16. MCP servers

**demisto-sdk 1.39.9+ and XSIAM 4.0: `mcps` on the agent.** An agent can now declare MCP
servers itself:

```yaml
mcps:
  - server_url: https://cortex-docs.paloaltonetworks.com/~gitbook/mcp
```

`server_url` is the only field, and it is required. The schema has no auth field, so this
suits unauthenticated servers.* Uploaded to a 4.0 tenant, the agent read back with `mcps`
intact. No built-in agent on that tenant uses the field, and generated `mcp_*` actions were
not checked during the test. So whether the agent discovers and calls the server's tools at runtime is untested.* The
rest of this section, binding instance-generated action ids, is the 8.15-era route and
still works. It is the only one that supports authenticated servers.

The original finding follows.

An agent CAN call an MCP server. It is native, needs no skill, and needs no pack content -
but it is tenant configuration, not content, and cannot be authored in a pack.

**Content side.** MCP is one boolean on an integration: `script.mcp: true`
(`schemas/integration.yml`). There is no MCP content type. Effects: `PackTags.MCP` is
auto-applied to the pack, and IN168 forces `marketplaces: [platform]` (auto-fixable).
Marketplace ships 5 such packs - `GenericMCP`, `GitHubMCP`, `AtlassianCloudMCP`,
`CloudflareMCP`, `ServiceNowMCP` - each containing exactly ONE integration and no other
content item.

**Cortex is the MCP client.** `Generic MCP` connects out to a server and discovers its
tools. Config: `base_url`, `auth_type`, plus credential fields. `auth_type` accepts Basic,
Token, Bearer, Api-Key, RawToken, `No Authorization`, and OAuth 2.0 Authorization Code /
Client Credentials / Dynamic Client Registration.

**Two undeclared, platform-reserved commands.** The integration yml declares only
`generic-mcp-auth-test` and `generic-mcp-generate-login-url`, but its `main()` also
dispatches `list-tools` and `call-tool`. Neither appears anywhere in the SDK - the
contract is platform-side only. `call-tool` takes a tool `name` plus a JSON `arguments`
string.

**Actions are generated by the platform, not authored.** Configuring an MCP instance makes
every discovered tool appear as an AgentixAction, selectable in the agent editor:

```
id           mcp_<Integration_Id>_<Instance_Name>_<toolName>   (spaces -> underscores)
display      <server advertised name> - <toolName> - <instance name>
description  [External MCP tool - <server name>] <the tool's own description>
underlying   {"id": "<Integration>-<Instance>-<tool>", "name": "<tool>",
              "type": "MCP Tool", "command": "", "instance": "<Instance>"}
isSystem     true
packID       ""            (platform-owned, belongs to no pack)
approval     true          (default on every generated tool, including read-only ones)
outputs      null          (MCP actions declare NONE - contrast: prompt needs exactly 1)
```

Args come from the tool's own JSON schema: name, type, required flag and description are
carried across, `underlyingargname` equals the tool's parameter name, and
`isgeneratable` is false on all of them.

**Why a pack cannot ship this.** Two reasons: GR110 rejects `type: MCP Tool`, and the
binding names a specific instance (`"instance": "Cortex Docs MCP"`), which is tenant
configuration and not portable.

**A pack agent CAN bind to them anyway.** Verified live: put the generated ids straight
into the agent's `actionids` and upload. The server keeps them, the actions attach, and
they report `live`. `validate` passes - nothing checks that an `actionids` entry resolves
to something in the pack. So the split is:

- the ACTION is tenant configuration, generated by the platform, unpackageable
- the AGENT that uses it is content, and ships in a pack

This is the only way to put MCP tools on an agent from a pack. The binding is by id, and
the id embeds the instance name, so the agent resolves its MCP tools only on a tenant
carrying an instance of exactly that name; elsewhere the ids are inert. Standardise the
instance name across tenants if you rely on this.

Skill bodies may reference them with `<action=mcp_...>` like any other action, and AG116
is satisfied because the ids are in `actionids`.

**Generated MCP actions ARE editable, despite looking locked.** Every one arrives with
`requiresUserApproval: true`, including read-only tools, and carries `isLocked: true` -
the only actions on the tenant that do (4 of 123). That lock is cosmetic: POSTing the
action object back to `/xsoar/agentix/action` with the field flipped returns 200 and
sticks (version 1 -> 2), leaving `underlyingContentItem`, args and display name intact.
`isLocked` stays `true` and `isDetailsOverridden` stays `false` after the edit, so neither
flag tracks editability - do not read them as "read-only".

```
POST /xsoar/agentix/action   <the full action object, one field changed>
```

This is the only way to clear the approval prompt on an MCP tool, since the action is not
pack content. Whether the change survives the platform re-discovering the server's tools
(instance re-save, tool refresh) is untested.*

Observed with the Cortex documentation MCP
(`https://cortex-docs.paloaltonetworks.com/~gitbook/mcp`, no auth), which exposes
`askQuestion`, `getPage`, `searchDocumentation` and `sendFeedback`.
