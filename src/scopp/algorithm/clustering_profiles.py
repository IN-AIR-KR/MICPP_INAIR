"""Interchangeable clustering strategies for SCoPP partitioning."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Protocol

from sklearn.cluster import MiniBatchKMeans

from scopp.config import ClusteringProfile
from scopp.map.models import NodeStart, XY


@dataclass(frozen=True, slots=True)
class RawClustering:
    centroids: tuple[XY, ...]
    labels: tuple[int, ...]
    node_ids: tuple[str, ...]
    iterations: int
    converged: bool
    random_seed: int | None


class Clusterer(Protocol):
    profile: ClusteringProfile

    def fit(self, points: tuple[XY, ...], nodes: tuple[NodeStart, ...], *, tolerance_m: float, max_iterations: int, random_seed: int) -> RawClustering: ...


def _nearest(point: XY, centroids: tuple[XY, ...]) -> int:
    return min(range(len(centroids)), key=lambda index: ((point[0] - centroids[index][0]) ** 2 + (point[1] - centroids[index][1]) ** 2, index))


def lloyd_cluster(points: tuple[XY, ...], initial_centroids: tuple[XY, ...], *, tolerance_m: float, max_iterations: int = 10) -> tuple[tuple[XY, ...], tuple[int, ...], int, bool]:
    if not points:
        raise ValueError("at least one perimeter sample is required")
    if not initial_centroids:
        raise ValueError("at least one node centroid is required")
    if tolerance_m <= 0 or max_iterations <= 0:
        raise ValueError("tolerance and max_iterations must be greater than zero")
    centroids = initial_centroids
    for iteration in range(1, max_iterations + 1):
        labels = tuple(_nearest(point, centroids) for point in points)
        updated: list[XY] = []
        for index, old in enumerate(centroids):
            members = tuple(point for point, label in zip(points, labels) if label == index)
            updated.append((sum(p[0] for p in members) / len(members), sum(p[1] for p in members) / len(members)) if members else old)
        next_centroids = tuple(updated)
        movement = max(hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(centroids, next_centroids))
        centroids = next_centroids
        if movement <= tolerance_m:
            return centroids, tuple(_nearest(point, centroids) for point in points), iteration, True
    return centroids, tuple(_nearest(point, centroids) for point in points), max_iterations, False


class DeterministicLloydClusterer:
    profile = ClusteringProfile.DETERMINISTIC_LLOYD

    def fit(self, points, nodes, *, tolerance_m, max_iterations, random_seed) -> RawClustering:
        centroids, labels, iterations, converged = lloyd_cluster(points, tuple(node.position for node in nodes), tolerance_m=tolerance_m, max_iterations=max_iterations)
        return RawClustering(centroids, labels, tuple(node.id for node in nodes), iterations, converged, None)


class OfficialMiniBatchClusterer:
    profile = ClusteringProfile.OFFICIAL_MINIBATCH

    def fit(self, points, nodes, *, tolerance_m, max_iterations, random_seed) -> RawClustering:
        estimator = MiniBatchKMeans(n_clusters=len(nodes), max_iter=max_iterations, tol=tolerance_m, batch_size=100, n_init=3, random_state=random_seed)
        predicted = estimator.fit_predict(points)
        centroids = tuple((float(center[0]), float(center[1])) for center in estimator.cluster_centers_)
        labels = tuple(int(label) for label in predicted)
        remaining = list(enumerate(nodes))
        associated: list[str] = []
        for cluster_index in range(len(centroids)):
            members = tuple(point for point, label in zip(points, labels) if label == cluster_index)
            if not members:
                raise ValueError(f"official_minibatch produced empty cluster {cluster_index}")
            chosen = min(range(len(remaining)), key=lambda offset: (min((p[0] - remaining[offset][1].position[0]) ** 2 + (p[1] - remaining[offset][1].position[1]) ** 2 for p in members), remaining[offset][0]))
            associated.append(remaining.pop(chosen)[1].id)
        return RawClustering(centroids, labels, tuple(associated), int(estimator.n_iter_), int(estimator.n_iter_) < max_iterations, random_seed)


_CLUSTERERS: dict[ClusteringProfile, Clusterer] = {
    ClusteringProfile.DETERMINISTIC_LLOYD: DeterministicLloydClusterer(),
    ClusteringProfile.OFFICIAL_MINIBATCH: OfficialMiniBatchClusterer(),
}


def get_clusterer(profile: ClusteringProfile | str) -> Clusterer:
    try:
        return _CLUSTERERS[ClusteringProfile(profile)]
    except (KeyError, ValueError) as exc:
        raise ValueError(f"unknown clustering profile: {profile}") from exc
