from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .utils import sha256_file


@dataclass
class ArtifactRef:
    path: str
    sha256: str
    type: Optional[str] = None
    schema_version: Optional[str] = None

    @classmethod
    def from_path(cls, base_dir, path, type: Optional[str] = None) -> "ArtifactRef":
        from pathlib import Path

        path = Path(path)
        digest = sha256_file(path)
        try:
            rel = path.relative_to(base_dir)
        except Exception:
            rel = path
        return cls(path=str(rel), sha256=digest, type=type)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"path": self.path, "sha256": self.sha256}
        if self.type:
            data["type"] = self.type
        if self.schema_version:
            data["schema_version"] = self.schema_version
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArtifactRef":
        return cls(path=data["path"], sha256=data["sha256"], type=data.get("type"), schema_version=data.get("schema_version"))


@dataclass
class RunManifest:
    run_id: str
    created_at: str
    config: Dict[str, Any]
    events: Dict[str, Any]
    ct_config: Optional[Dict[str, Any]] = None
    drift_config: Optional[Dict[str, Any]] = None
    cohort_id: Optional[str] = None
    edition: Optional[str] = None
    tag: Optional[str] = None
    git_commit: Optional[str] = None
    status: str = "SUCCESS"
    artifacts: Dict[str, str] = field(default_factory=dict)
    schema_version: str = "1.0"
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "config": self.config,
            "events": self.events,
            "ct_config": self.ct_config,
            "drift_config": self.drift_config,
            "cohort_id": self.cohort_id,
            "edition": self.edition,
            "tag": self.tag,
            "git_commit": self.git_commit,
            "status": self.status,
            "artifacts": self.artifacts,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunManifest":
        return cls(
            run_id=data["run_id"],
            created_at=data["created_at"],
            config=data["config"],
            events=data["events"],
            ct_config=data.get("ct_config"),
            drift_config=data.get("drift_config"),
            cohort_id=data.get("cohort_id"),
            edition=data.get("edition"),
            tag=data.get("tag"),
            git_commit=data.get("git_commit"),
            status=data.get("status", "SUCCESS"),
            artifacts=data.get("artifacts", {}),
            schema_version=data.get("schema_version", "1.0"),
            meta=data.get("meta", {}),
        )


@dataclass
class ProofManifest:
    run_id: str
    created_at: str
    artifacts: List[ArtifactRef]
    verification: Dict[str, Any] = field(default_factory=lambda: {"status": "PENDING", "details": "generated"})
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "verification": self.verification,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProofManifest":
        return cls(
            run_id=data["run_id"],
            created_at=data["created_at"],
            artifacts=[ArtifactRef.from_dict(a) for a in data.get("artifacts", [])],
            verification=data.get("verification", {}),
            schema_version=data.get("schema_version", "1.0"),
        )
