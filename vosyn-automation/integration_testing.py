import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.turso_data_manager import TursoDataManager
from src.config import Config
from src.playbooks.symplicity_playbook import SymplicityPlaybook


def print_banner(text):
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)
    print()


def main():
    print_banner("END-TO-END INTEGRATION TEST")

    em = TursoDataManager()

    
    print("Step 1: Reading queued jobs from Excel")
    queued_jobs = em.get_queued_jobs()
    if not queued_jobs:
        print("No queued jobs found! Please add a job with Status=QUEUED.")
        return

    print(f"Found {len(queued_jobs)} queued job(s)\n")

    job = queued_jobs[0]
    job_id = job["JobId"]
    print(f"  Job ID:   {job_id}")
    print(f"  Title:    {job['Title']}")
    print(f"  Location: {job['Location']}\n")

    
    print("Step 2: Transitioning job to RUNNING")
    if not em.transition_job_status(job_id, "QUEUED", "RUNNING", "WORKER_TEST"):
        print("Failed to lock job (someone else got it first).")
        return
    print("Job locked!\n")

    
    print("Step 3: Getting posting runs for this job")
    runs = em.get_queued_runs(job_id)
    if not runs:
        print("No queued runs found!")
        return
    print(f"Found {len(runs)} queued run(s)\n")

    
    for run in runs:
        run_id = run["RunId"]
        portal_name = run["PortalName"]
        portal_url = run["PortalUrl"]

        print_banner(f"Processing: {portal_name}")
        print(f"  Run ID:  {run_id}")
        print(f"  Portal:  {portal_name}")
        print(f"  URL:     {portal_url}\n")

        print("Step 4: Getting credentials")
        credentials = Config.get_credentials(portal_name)

        print("Step 5: Running automation")
        playbook = SymplicityPlaybook(
            portal_url=portal_url,
            credentials=credentials,
            job_data={
                "JobId": job_id,
                "Title": job["Title"],
                "Description": job["Description"],
                "Location": job["Location"],
                "Salary": job.get("Salary", ""),
                "portal_name": portal_name,
            },
        )
        result = playbook.execute()

        print("\nStep 6: Updating Excel with results")
        if result["status"] == "POSTED":
            em.update_posting_run(
                run_id=run_id,
                status="POSTED",
                portal_posting_id=result.get("confirmation_id"),
                proof_link=result.get("screenshot_path"),
            )
            print("  Updated run as POSTED")
        else:
            em.update_posting_run(
                run_id=run_id,
                status="FAILED",
                error_reason=result.get("error"),
            )
            print("  Updated run as FAILED")

    
    print("\nStep 7: Finalizing job status")
    final_status = em.finalize_job_status(job_id)

    print_banner("INTEGRATION TEST COMPLETE")
    print(f"  Job:          {job_id}")
    print(f"  Final Status: {final_status}\n")
    print("Check your Excel file to see the updates.")


if __name__ == "__main__":
    main()
