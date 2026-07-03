/**
 * ResumeMind — History Page JavaScript
 * Handles: loading history, rendering cards, viewing details, deleting records
 */

document.addEventListener("DOMContentLoaded", () => {
    const loadingState = document.getElementById("loading-state");
    const emptyState = document.getElementById("empty-state");
    const historyList = document.getElementById("history-list");
    const detailModal = document.getElementById("detail-modal");
    const modalClose = document.getElementById("modal-close");
    const modalBody = document.getElementById("modal-body");

    // =========================
    // Load History on Page Load
    // =========================

    loadHistory();

    async function loadHistory() {
        loadingState.hidden = false;
        emptyState.hidden = true;
        historyList.hidden = true;

        try {
            const response = await fetch("/api/history?limit=50&page=1");
            const data = await response.json();

            loadingState.hidden = true;

            if (data.status === "success" && data.history.length > 0) {
                renderHistoryCards(data.history);
                historyList.hidden = false;
            } else {
                emptyState.hidden = false;
            }
        } catch (err) {
            loadingState.hidden = true;
            emptyState.hidden = false;
            console.error("Failed to load history:", err);
        }
    }

    // =========================
    // Render History Cards
    // =========================

    function renderHistoryCards(history) {
        historyList.innerHTML = "";

        history.forEach((item, index) => {
            const card = document.createElement("div");
            card.className = "history-card";
            card.style.animationDelay = `${index * 0.05}s`;
            card.dataset.id = item.analysis_id;

            const date = formatDate(item.created_at);
            const topScore = item.top_candidate
                ? `${item.top_candidate.match_percentage}%`
                : "N/A";
            const topFile = item.top_candidate
                ? item.top_candidate.filename
                : "—";

            card.innerHTML = `
                <div class="history-card-top">
                    <div class="history-card-info">
                        <h3>${date}</h3>
                        <div class="history-card-meta">
                            <span>📄 ${item.total_resumes} resume${item.total_resumes > 1 ? "s" : ""}</span>
                            <span>🏆 Top: ${topFile}</span>
                        </div>
                    </div>
                    <div class="history-card-actions">
                        <button class="history-delete-btn" data-id="${item.analysis_id}" title="Delete">🗑️ Delete</button>
                    </div>
                </div>
                <p class="history-snippet">${item.job_description_snippet || "No description"}</p>
                <div class="history-card-bottom">
                    <span class="top-candidate-label">Best Match</span>
                    <span class="top-candidate-score">${topScore}</span>
                </div>
            `;

            // Click card to view details
            card.addEventListener("click", (e) => {
                // Don't open modal if clicking delete button
                if (e.target.closest(".history-delete-btn")) return;
                viewDetail(item.analysis_id);
            });

            historyList.appendChild(card);
        });

        // Add delete handlers
        historyList.querySelectorAll(".history-delete-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                if (confirm("Are you sure you want to delete this analysis?")) {
                    deleteAnalysis(id);
                }
            });
        });
    }

    // =========================
    // View Analysis Detail
    // =========================

    async function viewDetail(analysisId) {
        try {
            const response = await fetch(`/api/history/${analysisId}`);
            const data = await response.json();

            if (data.status !== "success") {
                alert(data.message || "Failed to load details.");
                return;
            }

            renderModal(data);
            detailModal.hidden = false;
        } catch (err) {
            alert("Network error. Could not load details.");
        }
    }

    function renderModal(data) {
        const date = formatDate(data.created_at);
        let html = `
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                📅 ${date} · 📄 ${data.total_resumes} resume${data.total_resumes > 1 ? "s" : ""}
            </p>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem; line-height: 1.6;">
                "${data.job_description_snippet}"
            </p>
        `;

        if (data.results && data.results.length > 0) {
            data.results.forEach((result, index) => {
                const pct = result.match_percentage;
                const level = pct >= 70 ? "high" : pct >= 40 ? "medium" : "low";
                const rankClass = (index + 1) <= 3 ? `rank-${index + 1}` : "rank-default";

                const skillsHTML = result.matched_skills && result.matched_skills.length > 0
                    ? result.matched_skills.map(s => `<span class="skill-badge">${s}</span>`).join("")
                    : `<span class="no-skills">No matching skills</span>`;

                html += `
                    <div class="result-card" style="margin-bottom: 0.75rem;">
                        <div class="result-card-header">
                            <div class="result-rank">
                                <div class="rank-badge ${rankClass}">#${index + 1}</div>
                                <span class="result-filename">${result.candidate_filename}</span>
                            </div>
                            <div class="result-percentage ${level}">${pct}%</div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill ${level}" style="width: ${pct}%;"></div>
                        </div>
                        <div class="skills-section">${skillsHTML}</div>
                    </div>
                `;
            });
        }

        modalBody.innerHTML = html;
    }

    // =========================
    // Delete Analysis
    // =========================

    async function deleteAnalysis(analysisId) {
        try {
            const response = await fetch(`/api/history/${analysisId}`, {
                method: "DELETE",
            });
            const data = await response.json();

            if (data.status === "success") {
                // Remove the card from DOM
                const card = historyList.querySelector(`[data-id="${analysisId}"]`);
                if (card) {
                    card.style.opacity = "0";
                    card.style.transform = "translateX(-20px)";
                    card.style.transition = "all 0.3s ease";
                    setTimeout(() => {
                        card.remove();
                        // Check if list is now empty
                        if (historyList.children.length === 0) {
                            historyList.hidden = true;
                            emptyState.hidden = false;
                        }
                    }, 300);
                }
            } else {
                alert(data.message || "Failed to delete analysis.");
            }
        } catch (err) {
            alert("Network error. Could not delete analysis.");
        }
    }

    // =========================
    // Modal Controls
    // =========================

    modalClose.addEventListener("click", () => {
        detailModal.hidden = true;
    });

    detailModal.addEventListener("click", (e) => {
        if (e.target === detailModal) {
            detailModal.hidden = true;
        }
    });

    // Close modal on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !detailModal.hidden) {
            detailModal.hidden = true;
        }
    });

    // =========================
    // Utility
    // =========================

    function formatDate(isoString) {
        if (!isoString) return "Unknown date";
        const d = new Date(isoString);
        return d.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }
});
