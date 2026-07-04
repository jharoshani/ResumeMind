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

                // Matched skills badges
                const skillsHTML = result.matched_skills && result.matched_skills.length > 0
                    ? result.matched_skills.map(s => `<span class="skill-badge">${s}</span>`).join("")
                    : `<span class="no-skills">No matching skills</span>`;

                // Missing skills badges
                const missingSkillsHTML = result.missing_skills && result.missing_skills.length > 0
                    ? result.missing_skills.map(s => `<span class="missing-badge">${s}</span>`).join("")
                    : `<span class="no-skills" style="color: var(--success);">All core skills matched!</span>`;

                // Coaching Tips
                let coachingCardsHTML = "";
                if (result.warnings && result.warnings.length > 0) {
                    result.warnings.forEach(w => {
                        coachingCardsHTML += `<div class="coaching-card warning">⚠️ ${w}</div>`;
                    });
                }
                if (result.coaching_tips && result.coaching_tips.length > 0) {
                    result.coaching_tips.forEach(c => {
                        coachingCardsHTML += `<div class="coaching-card info">💡 ${c}</div>`;
                    });
                }
                if (!coachingCardsHTML) {
                    coachingCardsHTML = `<div class="coaching-card info" style="background: rgba(34, 197, 94, 0.05); border-left: 3px solid var(--success); color: #a7f3d0;">🎉 Outstanding formatting and quality structure! No changes recommended.</div>`;
                }

                // Breakdown progress widths
                const corePct = result.breakdown ? (result.breakdown.core / 40.0) * 100 : 0;
                const expPct = result.breakdown ? (result.breakdown.experience / 30.0) * 100 : 0;
                const qualPct = result.breakdown ? (result.breakdown.quality / 20.0) * 100 : 0;
                const formatPct = result.breakdown ? (result.breakdown.format / 10.0) * 100 : 0;

                html += `
                    <div class="result-card" style="margin-bottom: 1.25rem;">
                        <div class="result-card-header">
                            <div class="result-rank">
                                <div class="rank-badge ${rankClass}">#${index + 1}</div>
                                <span class="result-filename">${result.candidate_filename || result.filename}</span>
                            </div>
                            <div class="result-percentage ${level}">${pct}%</div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill ${level}" style="width: ${pct}%;"></div>
                        </div>
                        
                        <div class="skills-section">
                            ${skillsHTML}
                        </div>

                        <!-- Toggle details button -->
                        <div class="detail-toggle-container">
                            <button class="detail-toggle-btn" id="modal-toggle-btn-${index}">
                                <span>Diagnostics & Optimizer Plan</span>
                                <span class="arrow">▼</span>
                            </button>
                        </div>

                        <!-- Collapsible detail drawer -->
                        <div class="detail-drawer" id="modal-drawer-${index}" hidden>
                            <!-- Sub-Scores breakdown -->
                            <div class="sub-score-grid">
                                <div class="sub-score-item">
                                    <div class="sub-score-info">
                                        <span class="sub-score-title">Core Match</span>
                                        <span class="sub-score-pct">${result.breakdown ? result.breakdown.core : 0} / 40</span>
                                    </div>
                                    <div class="sub-score-track">
                                        <div class="sub-score-fill" style="width: ${corePct}%"></div>
                                    </div>
                                </div>
                                <div class="sub-score-item">
                                    <div class="sub-score-info">
                                        <span class="sub-score-title">Experience & Tenure</span>
                                        <span class="sub-score-pct">${result.breakdown ? result.breakdown.experience : 0} / 30</span>
                                    </div>
                                    <div class="sub-score-track">
                                        <div class="sub-score-fill" style="width: ${expPct}%"></div>
                                    </div>
                                </div>
                                <div class="sub-score-item">
                                    <div class="sub-score-info">
                                        <span class="sub-score-title">Impact Quality</span>
                                        <span class="sub-score-pct">${result.breakdown ? result.breakdown.quality : 0} / 20</span>
                                    </div>
                                    <div class="sub-score-track">
                                        <div class="sub-score-fill" style="width: ${qualPct}%"></div>
                                    </div>
                                </div>
                                <div class="sub-score-item">
                                    <div class="sub-score-info">
                                        <span class="sub-score-title">Formatting</span>
                                        <span class="sub-score-pct">${result.breakdown ? result.breakdown.format : 0} / 10</span>
                                    </div>
                                    <div class="sub-score-track">
                                        <div class="sub-score-fill" style="width: ${formatPct}%"></div>
                                    </div>
                                </div>
                            </div>

                            <!-- Missing requirements -->
                            <div class="missing-section">
                                <h4>❌ Missing Target Requirements</h4>
                                <div class="missing-badges-container">
                                    ${missingSkillsHTML}
                                </div>
                            </div>

                            <!-- Optimization Advice list -->
                            <div class="coaching-section">
                                <h4>💡 Optimization Action Plan</h4>
                                <div class="coaching-list">
                                    ${coachingCardsHTML}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        modalBody.innerHTML = html;

        // Attach event listeners to toggle buttons in the modal after rendering HTML
        if (data.results && data.results.length > 0) {
            data.results.forEach((result, index) => {
                const toggleBtn = modalBody.querySelector(`#modal-toggle-btn-${index}`);
                const drawer = modalBody.querySelector(`#modal-drawer-${index}`);
                if (toggleBtn && drawer) {
                    toggleBtn.addEventListener("click", () => {
                        const isHidden = drawer.hidden;
                        drawer.hidden = !isHidden;
                        toggleBtn.classList.toggle("expanded", isHidden);
                    });
                }
            });
        }
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
