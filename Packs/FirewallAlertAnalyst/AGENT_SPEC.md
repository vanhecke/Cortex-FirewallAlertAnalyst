# Agentix agent spec

What a pack must contain for an Agentix agent to validate and to work on a tenant.

Sources: demisto-sdk v1.39.6 (HEAD `baa008469`) - its schemas, strict objects, parsers,
preparers and AG/GR validators, plus its git history - and live deploys of
`FirewallAlertAnalyst` to Cortex XSIAM tenants. File paths below are relative to a
demisto-sdk checkout.

`*` marks anything not verified end to end.

---

## 1. Content types

| Type | Pack dir | Server name | Uploaded |
| --- | --- | --- | --- |
| AgentixAgent | `AgentixAgents/` | `agentixagent` | yes |
| AgentixAction | `AgentixActions/` | `agentixaction` | yes |
| AgentixActionTest | `AgentixActions/` | - | **no** (`CONTENT_TYPES_EXCLUDED_FROM_UPLOAD`) |
| AgentixSkill | `AgentixSkills/` | `agentixskill` | yes |
| Collection | `Collections/` | `agentixknowledgecollection` | yes (name/description only, see 11) |
| Script | `Scripts/` | `automation` | yes |

Release-note headers: `Agents`, `Actions`, `Skills`, `Collections`.

## 2. File layout

```
Packs/<Pack>/
  pack_metadata.json
  AgentixAgents/<AgentId>/<AgentId>.yml
                          <AgentId>_systeminstructions.md   MANDATORY (AG110)
  AgentixActions/<ActionId>/<ActionId>.yml
                            <ActionId>_test.yml             MANDATORY (AG118)
  AgentixSkills/<SkillId>/<SkillId>.yml
                          <SkillId>_skill.md                MANDATORY (AG111)
  Collections/<CollectionId>/<CollectionId>.yml
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
| `collectionids` | no | Collection ids |
| `builtinactions` | no | platform capability names, see 9 |
| `conversationstarters` | no | list of strings |
| `autoenablenewactions` | no | bool |
| `roles`, `sharedwithroles` | no | RBAC |
| `category`, `tags` | no | AG102 constrains `category` |
| `marketplaces` | no | must be `[platform]` (AG101) |
| `supportedModules` | no | `[agentix]` |

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
| `marketplaces` | no | `[platform]` (AG101) |

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

## 11. Collection

Schema `common/schemas/collection.yml`. Required: `commonfields.id`/`.version`, `name`.
Optional: `description`, `fromversion`, `toversion`, `marketplaces`, `supportedModules`,
per-marketplace `name:<mp>` / `description:<mp>`.

There is **no** content, body, documents, text, files or knowledge field. A pack-carried
collection is a dangling reference: upload registers the id on the agent
(`systemKnowledgeCollectionIds`) but creates no collection object -
`GET /xsoar/agentix/knowledgecollections` returns `[]` and the agent's `QueryUserKnowledge`
returns `references: []`. The `description` is not retrievable content. Documents must be
created tenant-side; `POST /xsoar/agentix/knowledgecollection` is the likely route (it
exists - GET returns 405).* UNRESOLVED.

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

`promptConfig`: `temperature`, `maxOutputTokens`, `webSearch`. Note `fewshots` on a script
is a **string**; on an action it is a list of strings.

Server rules the SDK does not encode, all verified live:

- `model` is mandatory in practice. `promptConfig` names no LLM, and the validator accepts
  `promptConfig` alone. Without `model` the action registers, reports `live`, and returns
  HTTP 500 on invoke.
- Exactly one output required: `'Outputs' attribute must have 1 value (52)`.
- `temperature` is rejected by models that do not list it in `supportedParams`.
  `claude-opus-4-8` takes `maxTokens`/`stopSequences`/`thinking`/`outputConfig` but not
  `temperature`; `claude-sonnet-4-6` takes it. Wrong param = HTTP 500.

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

AG112 and AG117 are in the SDK's `ignorable_errors`, so `.pack-ignore` can silence them.

**Run `validate` with a config or it checks nothing.** The SDK's `default_config.toml`
selects 15 codes and **no** AG or GR rule at all, so an unconfigured run leaves the agent,
actions and skills entirely unchecked. Its `sdk_validation_config.toml` does select them,
but assumes a checkout of demisto/content and aborts on a standalone pack (PA102 fetches
`approved_categories.json`).

This repo therefore ships its own `validation_config.toml` at the root:

```
demisto-sdk validate -i Packs/FirewallAlertAnalyst --config-path validation_config.toml
```

It selects AG101, AG103-AG111, AG114, AG115, AG117 and AG118. Deliberately not selected:
AG100 and AG102 (need a remote fetch), AG112 (character budgets - enable it if your skill
bodies are hand-written), AG116 and all GR rules (need a populated content graph, which
`upload` does not build), and DO104 (raises rather than fails on prompt scripts, which have
no `dockerimage`).

## 14. Other server behaviour

- Content cannot be read back to verify. `systemInstructions` returns encrypted
  (`{MULAN}...`), and only `/xsoar/agentix/agents`, `/actions` and
  `/knowledgecollections` respond - there is no endpoint for skills, collections or
  prompts.
- Support varies by tenant version. On an older tenant a prompt-backed action installed
  dead (`underlying content item ... of type [prompt] was not found`) and the agent object
  carried no `skillIds` or `systemKnowledgeCollectionIds` at all.
- Pack uninstall works and is asynchronous:
  `POST /xsoar/contentpacks/installed/delete {"IDs":["<pack>"]}` returns `200 {}`
  immediately; the pack and every item it materialized disappear within ~1 minute.
- Ids are identity. Renaming an id creates a new object and orphans the old one; uninstall
  the pack before re-uploading renamed content.

## 15. Reference implementation

`Packs/FirewallAlertAnalyst` exercises `command` (with a named integration and with
`_any_`), `script` and `prompt` underlying types, both `_test.yml` evaluation modes,
`<action=...>` tokens, a collection handle and the full arg/output flag set. See its
README.

## 16. MCP servers

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
