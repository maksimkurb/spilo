#!/usr/bin/env python3
"""
Script to update VectorChord version in Spilo Dockerfile
"""

import json
import re
import subprocess
import sys
from typing import List, Optional

import requests


def run_git_command(cmd: List[str]) -> tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def fetch_vectorchord_releases() -> Optional[List[str]]:
    """Fetch available VectorChord releases from GitHub API."""
    try:
        url = "https://api.github.com/repos/tensorchord/VectorChord/releases"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        releases = response.json()
        versions = []
        
        for release in releases:
            if not release.get("prerelease", False) and not release.get("draft", False):
                tag_name = release["tag_name"]
                # Remove 'v' prefix if present
                version = tag_name.lstrip('v')
                versions.append(version)
        
        return versions[:20]  # Limit to 20 most recent releases
    
    except requests.RequestException as e:
        print(f"Error fetching VectorChord releases: {e}")
        return None


def select_version(versions: List[str]) -> Optional[str]:
    """Display version list and get user selection."""
    print("\nAvailable VectorChord versions:")
    for i, version in enumerate(versions, 1):
        print(f"{i:2d}. {version}")
    
    while True:
        try:
            choice = input(f"\nSelect version (1-{len(versions)}): ").strip()
            if not choice:
                continue
            
            index = int(choice) - 1
            if 0 <= index < len(versions):
                return versions[index]
            else:
                print(f"Please enter a number between 1 and {len(versions)}")
        
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            return None


def update_dockerfile(version: str) -> bool:
    """Update VECTORCHORD version in Dockerfile."""
    dockerfile_path = "postgres-appliance/Dockerfile"
    
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Update VECTORCHORD version on line 4
        pattern = r'^ARG VECTORCHORD="[^"]*"'
        replacement = f'ARG VECTORCHORD="{version}"'
        
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if new_content == content:
            print("Warning: No VECTORCHORD version found to update")
            return False
        
        with open(dockerfile_path, 'w') as f:
            f.write(new_content)
        
        print(f"Updated Dockerfile: VECTORCHORD version set to {version}")
        return True
    
    except Exception as e:
        print(f"Error updating Dockerfile: {e}")
        return False


def main():
    """Main script execution."""
    print("VectorChord Version Update Script")
    print("=" * 35)
    
    # 1. Checkout main branch
    print("\n1. Checking out main branch...")
    success, output = run_git_command(["checkout", "main"])
    if not success:
        print(f"Error checking out main branch: {output}")
        sys.exit(1)
    print("✓ Successfully checked out main branch")
    
    # 2. Fetch VectorChord versions
    print("\n2. Fetching VectorChord releases from GitHub...")
    versions = fetch_vectorchord_releases()
    if not versions:
        print("Failed to fetch VectorChord versions")
        sys.exit(1)
    print(f"✓ Found {len(versions)} VectorChord releases")
    
    # 3. Get user selection
    selected_version = select_version(versions)
    if not selected_version:
        print("No version selected, exiting")
        sys.exit(1)
    
    print(f"\n✓ Selected VectorChord version: {selected_version}")
    
    # 4. Create new branch
    branch_name = f"4.0-master-vectorchord-{selected_version}"
    print(f"\n3. Creating branch: {branch_name}")
    
    success, output = run_git_command(["checkout", "-b", branch_name])
    if not success:
        print(f"Error creating branch: {output}")
        sys.exit(1)
    print(f"✓ Created and switched to branch: {branch_name}")
    
    # 5. Update Dockerfile
    print("\n4. Updating Dockerfile...")
    if not update_dockerfile(selected_version):
        print("Failed to update Dockerfile")
        sys.exit(1)
    
    # 6. Commit changes
    print("\n5. Committing changes...")
    success, output = run_git_command(["add", "postgres-appliance/Dockerfile"])
    if not success:
        print(f"Error adding Dockerfile: {output}")
        sys.exit(1)
    
    commit_msg = f"Update VectorChord to {selected_version}"
    success, output = run_git_command(["commit", "-m", commit_msg])
    if not success:
        print(f"Error committing changes: {output}")
        sys.exit(1)
    print(f"✓ Committed changes: {commit_msg}")
    
    # 7. Create tag
    tag_name = f"{branch_name}-1"
    print(f"\n6. Creating tag: {tag_name}")
    
    success, output = run_git_command(["tag", tag_name])
    if not success:
        print(f"Error creating tag: {output}")
        sys.exit(1)
    print(f"✓ Created tag: {tag_name}")
    
    # 8. Push branch and tag
    print("\n7. Pushing branch and tag to GitHub...")
    
    # Push branch
    success, output = run_git_command(["push", "-u", "origin", branch_name])
    if not success:
        print(f"Error pushing branch: {output}")
        sys.exit(1)
    print(f"✓ Pushed branch: {branch_name}")
    
    # Push tag
    success, output = run_git_command(["push", "origin", tag_name])
    if not success:
        print(f"Error pushing tag: {output}")
        sys.exit(1)
    print(f"✓ Pushed tag: {tag_name}")
    
    print(f"\n🎉 Successfully updated VectorChord to version {selected_version}")
    print(f"   Branch: {branch_name}")
    print(f"   Tag: {tag_name}")


if __name__ == "__main__":
    main()