"""
GitHub Client - Handles GitHub API interactions
"""
from github import Github
from typing import Optional, List, Dict
import os


class GitHubClient:
    """Wrapper for GitHub API operations"""
    
    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """
        Initialize GitHub client
        
        Args:
            token: GitHub personal access token
            repo_name: Repository name in format "owner/repo"
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo_name = repo_name or os.getenv('GITHUB_REPO')
        
        if not self.token:
            raise ValueError("GitHub token not provided")
        
        self.client = Github(self.token)
        self.repo = self.client.get_repo(self.repo_name) if self.repo_name else None
    
    def get_pr(self, pr_number: int) -> Dict:
        """
        Get PR information
        
        Args:
            pr_number: PR number
            
        Returns:
            Dictionary with PR information
        """
        pr = self.repo.get_pull(pr_number)
        
        # Get files
        files = []
        for file in pr.get_files():
            if file.filename.endswith('.sol'):
                content = None
                
                # For merged/closed PRs, branch might be deleted - use patch
                if pr.state == 'closed' and file.patch:
                    content = self._extract_content_from_patch(file.patch)
                else:
                    # Try to get content from branch
                    content = self._get_file_content(file.filename, pr.head.ref)
                    # Fallback to patch if branch fetch fails
                    if not content and file.patch:
                        content = self._extract_content_from_patch(file.patch)
                
                # Only add files that have content
                if content:
                    files.append({
                        'filename': file.filename,
                        'path': file.filename,
                        'content': content
                    })
        
        return {
            'number': pr.number,
            'title': pr.title,
            'description': pr.body or '',
            'author': pr.user.login,
            'files': files,
            'state': pr.state,
            'head_ref': pr.head.ref,
            'base_ref': pr.base.ref
        }
    
    def _get_file_content(self, file_path: str, ref: str) -> str:
        """Get content of a file from a specific ref"""
        try:
            content = self.repo.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except Exception:
            # Silently fail - will use patch instead
            return ""
    
    def _extract_content_from_patch(self, patch: str) -> str:
        """Extract file content from git patch"""
        lines = []
        for line in patch.split('\n'):
            # Skip patch metadata lines
            if line.startswith('@@') or line.startswith('---') or line.startswith('+++'):
                continue
            # Add lines that were added (start with +)
            if line.startswith('+'):
                lines.append(line[1:])  # Remove the + prefix
            # Also include context lines (no prefix)
            elif not line.startswith('-'):
                lines.append(line)
        return '\n'.join(lines)
    
    def post_review(self, pr_number: int, body: str, event: str = "COMMENT") -> None:
        """
        Post a review comment on PR
        
        Args:
            pr_number: PR number
            body: Review comment body
            event: Review event type (APPROVE, REQUEST_CHANGES, COMMENT)
        """
        pr = self.repo.get_pull(pr_number)
        pr.create_review(body=body, event=event)
    
    def add_labels(self, pr_number: int, labels: List[str]) -> None:
        """
        Add labels to PR
        
        Args:
            pr_number: PR number
            labels: List of label names
        """
        pr = self.repo.get_pull(pr_number)
        issue = self.repo.get_issue(pr_number)
        issue.add_to_labels(*labels)
    
    def post_comment(self, pr_number: int, comment: str) -> None:
        """
        Post a comment on PR
        
        Args:
            pr_number: PR number
            comment: Comment text
        """
        pr = self.repo.get_pull(pr_number)
        pr.create_issue_comment(comment)
    
    def merge_pr(self, pr_number: int, merge_method: str = "squash") -> bool:
        """
        Merge a PR
        
        Args:
            pr_number: PR number
            merge_method: Merge method (merge, squash, rebase)
            
        Returns:
            True if merged successfully, False otherwise
        """
        try:
            pr = self.repo.get_pull(pr_number)
            result = pr.merge(merge_method=merge_method)
            return result.merged
        except Exception as e:
            print(f"Error merging PR: {e}")
            return False
