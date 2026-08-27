# Milestone 2.1 — Create Lakebase Project + Dev Branch
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import (
    Project, ProjectSpec, Branch, BranchSpec
)

w = WorkspaceClient()

# Create project (autoscaling, PG 17)
op = w.postgres.create_project(
    project=Project(spec=ProjectSpec(display_name="Meridian Bank", pg_version=17)),
    project_id="meridian-bank",
)
project = op.wait()
print("Created:", project.name)

# Create dev branch (permanent, copy-on-write from production)
w.postgres.create_branch(
    parent="projects/meridian-bank",
    branch=Branch(spec=BranchSpec(
        source_branch="projects/meridian-bank/branches/production",
        no_expiry=True,
    )),
    branch_id="dev",
).wait()
print("Dev branch created")

# Verify connectivity
for b in w.postgres.list_branches(parent="projects/meridian-bank"):
    print(f"  {b.name} — state: {b.status.current_state}")
for e in w.postgres.list_endpoints(parent="projects/meridian-bank/branches/production"):
    print(f"  Endpoint host: {e.status.hosts.host}")
