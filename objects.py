"""Catalog of every JIRA object documented in the Salesforce Data Cloud
JIRA Structured Connector reference:
https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-jira-objects.html

Each entry maps the SF object name to the closest JIRA Cloud REST endpoint,
the HTTP method, and metadata used by the Streamlit UI to render an input
form and by ``jira_client`` to dispatch the request.

This catalog is intentionally read-only and additive: adding a new object is
a one-line edit. The runtime never mutates JIRA state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ObjectParam:
    """A parameter the user must (or may) supply to query an object."""

    name: str
    description: str
    required: bool = False
    placement: str = "path"  # "path" | "query"
    default: Optional[str] = None


@dataclass(frozen=True)
class JiraObject:
    """Definition of one JIRA object exposed by the SF connector."""

    name: str
    description: str
    endpoint: str  # may contain {placeholders}
    api: str = "platform"  # "platform" -> /rest/api/3, "agile" -> /rest/agile/1.0
    response_path: Optional[str] = None  # JSON key to flatten ("issues", "values"...)
    params: tuple[ObjectParam, ...] = field(default_factory=tuple)
    cloud_supported: bool = True
    notes: str = ""


_PARAM_ISSUE = ObjectParam(
    name="issueIdOrKey",
    description="Issue key (e.g. PROJ-123) or numeric ID",
    required=True,
)
_PARAM_PROJECT = ObjectParam(
    name="projectIdOrKey",
    description="Project key (e.g. PROJ) or numeric ID",
    required=True,
)
_PARAM_BOARD = ObjectParam(
    name="boardId",
    description="Numeric board ID",
    required=True,
)
_PARAM_SPRINT = ObjectParam(
    name="sprintId",
    description="Numeric sprint ID",
    required=True,
)
_PARAM_MAX = ObjectParam(
    name="maxResults",
    description="Page size (default 50)",
    required=False,
    placement="query",
    default="50",
)


CATALOG: dict[str, JiraObject] = {
    obj.name: obj
    for obj in [
        JiraObject(
            name="AdvancedSettings",
            description="Application properties from the JIRA Advanced Settings page.",
            endpoint="/application-properties",
        ),
        JiraObject(
            name="ApplicationRoles",
            description="All application roles configured in JIRA.",
            endpoint="/applicationrole",
        ),
        JiraObject(
            name="Attachments",
            description="Attachments on a single issue.",
            endpoint="/issue/{issueIdOrKey}",
            response_path="fields.attachment",
            params=(_PARAM_ISSUE,),
            notes="Returned as the 'attachment' field of an issue payload.",
        ),
        JiraObject(
            name="Audit",
            description="Audit log records for the JIRA account.",
            endpoint="/auditing/record",
            response_path="records",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="BoardConfiguration",
            description="Configuration of an Agile board.",
            endpoint="/board/{boardId}/configuration",
            api="agile",
            params=(_PARAM_BOARD,),
        ),
        JiraObject(
            name="BoardIssues",
            description="Issues currently on an Agile board.",
            endpoint="/board/{boardId}/issue",
            api="agile",
            response_path="issues",
            params=(_PARAM_BOARD, _PARAM_MAX),
        ),
        JiraObject(
            name="Boards",
            description="All Agile boards visible to the user.",
            endpoint="/board",
            api="agile",
            response_path="values",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="BoardSprints",
            description="Sprints belonging to an Agile board.",
            endpoint="/board/{boardId}/sprint",
            api="agile",
            response_path="values",
            params=(_PARAM_BOARD, _PARAM_MAX),
        ),
        JiraObject(
            name="Comments",
            description="Comments on a single issue.",
            endpoint="/issue/{issueIdOrKey}/comment",
            response_path="comments",
            params=(_PARAM_ISSUE, _PARAM_MAX),
        ),
        JiraObject(
            name="Configuration",
            description="Global JIRA configuration flags.",
            endpoint="/configuration",
        ),
        JiraObject(
            name="Dashboards",
            description="Dashboards available to the current user.",
            endpoint="/dashboard",
            response_path="dashboards",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="Epics",
            description="Epics on an Agile board.",
            endpoint="/board/{boardId}/epic",
            api="agile",
            response_path="values",
            params=(_PARAM_BOARD, _PARAM_MAX),
        ),
        JiraObject(
            name="FavouriteFilters",
            description="Filters favourited by the current user.",
            endpoint="/filter/favourite",
        ),
        JiraObject(
            name="Fields",
            description="All system and custom fields.",
            endpoint="/field",
        ),
        JiraObject(
            name="Filters",
            description="Saved filters available to the current user.",
            endpoint="/filter/search",
            response_path="values",
            params=(_PARAM_MAX,),
            notes="Not available on JIRA Server.",
        ),
        JiraObject(
            name="FiltersUsers",
            description="Users a given filter is shared with.",
            endpoint="/filter/{filterId}/permission",
            params=(
                ObjectParam(
                    name="filterId",
                    description="Numeric filter ID",
                    required=True,
                ),
            ),
        ),
        JiraObject(
            name="Groups",
            description="All groups, by name.",
            endpoint="/groups/picker",
            response_path="groups",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="GroupsUsers",
            description="Users in a specific group.",
            endpoint="/group/member",
            response_path="values",
            params=(
                ObjectParam(
                    name="groupname",
                    description="Group name to look up",
                    required=True,
                    placement="query",
                ),
                _PARAM_MAX,
            ),
        ),
        JiraObject(
            name="IssueAffectedVersions",
            description="Affected versions on an issue.",
            endpoint="/issue/{issueIdOrKey}",
            response_path="fields.versions",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="IssueChangelogs",
            description="Changelog entries for a single issue.",
            endpoint="/issue/{issueIdOrKey}/changelog",
            response_path="values",
            params=(_PARAM_ISSUE, _PARAM_MAX),
        ),
        JiraObject(
            name="IssueComponents",
            description="Components attached to an issue.",
            endpoint="/issue/{issueIdOrKey}",
            response_path="fields.components",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="IssueCustomFieldOptions",
            description="Options for a single custom field.",
            endpoint="/customField/{fieldId}/option",
            params=(
                ObjectParam(
                    name="fieldId",
                    description="Custom field ID (e.g. customfield_10010)",
                    required=True,
                ),
            ),
            cloud_supported=False,
            notes="Not available on JIRA Server or with OAuth auth.",
        ),
        JiraObject(
            name="IssueCustomFields",
            description="All custom fields (filtered subset of /field).",
            endpoint="/field",
            notes="Client filters to entries where 'custom' == true.",
        ),
        JiraObject(
            name="IssueFixVersions",
            description="Fix versions on an issue.",
            endpoint="/issue/{issueIdOrKey}",
            response_path="fields.fixVersions",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="IssueLinks",
            description="Links between issues for one issue.",
            endpoint="/issue/{issueIdOrKey}",
            response_path="fields.issuelinks",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="IssueLinkTypes",
            description="All available issue link types.",
            endpoint="/issueLinkType",
            response_path="issueLinkTypes",
        ),
        JiraObject(
            name="IssueNavigatorDefaultColumns",
            description="Default columns shown in the issue navigator.",
            endpoint="/settings/columns",
        ),
        JiraObject(
            name="IssuePriorities",
            description="All issue priorities.",
            endpoint="/priority",
        ),
        JiraObject(
            name="IssueResolutions",
            description="All issue resolutions.",
            endpoint="/resolution",
        ),
        JiraObject(
            name="Issues",
            description="Search issues with JQL.",
            endpoint="/search/jql",
            response_path="issues",
            params=(
                ObjectParam(
                    name="jql",
                    description=(
                        "JQL query - MUST be bounded (e.g. 'project = PROJ' or 'created >= -30d'). "
                        "Pure 'ORDER BY ...' queries are rejected by /search/jql with HTTP 400."
                    ),
                    required=True,
                    placement="query",
                    default="created >= -30d ORDER BY created DESC",
                ),
                ObjectParam(
                    name="fields",
                    description="Comma-separated fields to include (default returns common ones)",
                    required=False,
                    placement="query",
                    default="summary,status,priority,issuetype,assignee,reporter,created,updated",
                ),
                _PARAM_MAX,
            ),
            notes=(
                "Uses the new /search/jql endpoint (legacy /search returns HTTP 410 Gone since 2024). "
                "The new endpoint requires a bounded JQL query."
            ),
        ),
        JiraObject(
            name="IssueSecurityLevelMembers",
            description="Members assigned to issue security levels.",
            endpoint="/issuesecurityschemes/{schemeId}/members",
            params=(
                ObjectParam(
                    name="schemeId",
                    description="Issue security scheme ID",
                    required=True,
                ),
            ),
        ),
        JiraObject(
            name="IssueSubtasks",
            description="Subtasks of a parent issue (queried via JQL).",
            endpoint="/search/jql",
            response_path="issues",
            params=(
                ObjectParam(
                    name="jql",
                    description="JQL pre-filled to 'parent = <key>'",
                    required=True,
                    placement="query",
                    default="parent = PROJ-1",
                ),
                ObjectParam(
                    name="fields",
                    description="Comma-separated fields to include",
                    required=False,
                    placement="query",
                    default="summary,status,issuetype,parent",
                ),
                _PARAM_MAX,
            ),
            notes="Uses the new /search/jql endpoint (legacy /search returns HTTP 410 Gone since 2024).",
        ),
        JiraObject(
            name="IssueTransitions",
            description="Available workflow transitions for an issue.",
            endpoint="/issue/{issueIdOrKey}/transitions",
            response_path="transitions",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="IssueTypes",
            description="All issue types.",
            endpoint="/issuetype",
        ),
        JiraObject(
            name="MyPermissions",
            description="Permissions of the current user.",
            endpoint="/mypermissions",
            response_path="permissions",
        ),
        JiraObject(
            name="PermissionGrants",
            description="Permission grants for a permission scheme.",
            endpoint="/permissionscheme/{schemeId}/permission",
            response_path="permissions",
            params=(
                ObjectParam(
                    name="schemeId",
                    description="Permission scheme ID",
                    required=True,
                ),
            ),
        ),
        JiraObject(
            name="Permissions",
            description="All permission keys defined by JIRA.",
            endpoint="/permissions",
            response_path="permissions",
        ),
        JiraObject(
            name="PermissionSchemes",
            description="All permission schemes.",
            endpoint="/permissionscheme",
            response_path="permissionSchemes",
        ),
        JiraObject(
            name="ProjectCategories",
            description="All project categories.",
            endpoint="/projectCategory",
        ),
        JiraObject(
            name="ProjectComponents",
            description="Components of a single project.",
            endpoint="/project/{projectIdOrKey}/components",
            params=(_PARAM_PROJECT,),
        ),
        JiraObject(
            name="ProjectRoleActors",
            description="Actors in a role for a project.",
            endpoint="/project/{projectIdOrKey}/role/{roleId}",
            params=(
                _PARAM_PROJECT,
                ObjectParam(
                    name="roleId",
                    description="Role ID",
                    required=True,
                ),
            ),
        ),
        JiraObject(
            name="ProjectRoles",
            description="Roles available across projects.",
            endpoint="/role",
        ),
        JiraObject(
            name="Projects",
            description="All projects visible to the user.",
            endpoint="/project/search",
            response_path="values",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="ProjectsIssueTypes",
            description="Issue types per project.",
            endpoint="/issuetypescheme/project",
            response_path="values",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="ProjectsPermissionScheme",
            description="Permission scheme assigned to a project.",
            endpoint="/project/{projectIdOrKey}/permissionscheme",
            params=(_PARAM_PROJECT,),
        ),
        JiraObject(
            name="ProjectTypes",
            description="All project types (software, business, ...).",
            endpoint="/project/type",
        ),
        JiraObject(
            name="ProjectVersions",
            description="Versions defined on a project.",
            endpoint="/project/{projectIdOrKey}/versions",
            params=(_PARAM_PROJECT,),
        ),
        JiraObject(
            name="RoleActors",
            description="Default actors for project roles.",
            endpoint="/role/{roleId}/actors",
            response_path="actors",
            params=(
                ObjectParam(
                    name="roleId",
                    description="Role ID",
                    required=True,
                ),
            ),
        ),
        JiraObject(
            name="Roles",
            description="All roles.",
            endpoint="/role",
        ),
        JiraObject(
            name="SecurityLevels",
            description="All issue security levels.",
            endpoint="/issuesecurityschemes",
            response_path="issueSecuritySchemes",
        ),
        JiraObject(
            name="SecuritySchemes",
            description="All issue security schemes.",
            endpoint="/issuesecurityschemes",
            response_path="issueSecuritySchemes",
        ),
        JiraObject(
            name="SprintIssues",
            description="Issues belonging to a sprint.",
            endpoint="/sprint/{sprintId}/issue",
            api="agile",
            response_path="issues",
            params=(_PARAM_SPRINT, _PARAM_MAX),
        ),
        JiraObject(
            name="Sprints",
            description="Sprints on an Agile board.",
            endpoint="/board/{boardId}/sprint",
            api="agile",
            response_path="values",
            params=(_PARAM_BOARD, _PARAM_MAX),
        ),
        JiraObject(
            name="Statuses",
            description="All workflow statuses.",
            endpoint="/status",
        ),
        JiraObject(
            name="TimeTrackingProviders",
            description="Available time tracking providers.",
            endpoint="/configuration/timetracking/list",
        ),
        JiraObject(
            name="Users",
            description="All users (paginated).",
            endpoint="/users/search",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="Votes",
            description="Votes on a single issue.",
            endpoint="/issue/{issueIdOrKey}/votes",
            response_path="voters",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="Watchers",
            description="Watchers of a single issue.",
            endpoint="/issue/{issueIdOrKey}/watchers",
            response_path="watchers",
            params=(_PARAM_ISSUE,),
        ),
        JiraObject(
            name="Workflows",
            description="All workflows.",
            endpoint="/workflow/search",
            response_path="values",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="WorkflowSchemes",
            description="All workflow schemes.",
            endpoint="/workflowscheme",
            response_path="values",
            params=(_PARAM_MAX,),
        ),
        JiraObject(
            name="WorkflowStatusCategories",
            description="All status categories.",
            endpoint="/statuscategory",
        ),
        JiraObject(
            name="WorkflowStatuses",
            description="All statuses associated with workflows.",
            endpoint="/status",
        ),
        JiraObject(
            name="WorklogDeleted",
            description="Worklogs deleted since a given timestamp.",
            endpoint="/worklog/deleted",
            response_path="values",
        ),
        JiraObject(
            name="Worklogs",
            description="Worklogs on a single issue.",
            endpoint="/issue/{issueIdOrKey}/worklog",
            response_path="worklogs",
            params=(_PARAM_ISSUE, _PARAM_MAX),
        ),
    ]
}


def list_object_names() -> list[str]:
    """Return all catalog object names, alphabetically."""
    return sorted(CATALOG.keys())


def get(name: str) -> JiraObject:
    """Look up an object by name. Raises ``KeyError`` if unknown."""
    return CATALOG[name]
