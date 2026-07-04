/**
 * ResumeMind — Dashboard JavaScript
 * Handles: word counting, file upload, drag-drop, analysis submission, result rendering
 */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("analysis-form");
    const textarea = document.getElementById("job-description");
    const wordCounter = document.getElementById("word-counter");
    const wordLimitFill = document.getElementById("word-limit-fill");
    const fileInput = document.getElementById("file-input");
    const uploadZone = document.getElementById("upload-zone");
    const fileList = document.getElementById("file-list");
    const fileCounter = document.getElementById("file-counter");
    const submitBtn = document.getElementById("submit-btn");
    const errorContainer = document.getElementById("error-container");
    const errorMessage = document.getElementById("error-message");
    const resultsSection = document.getElementById("results-section");
    const resultsGrid = document.getElementById("results-grid");
    const resultsCount = document.getElementById("results-count");

    const MAX_WORDS = 200;
    const MAX_FILES = 10;
    let selectedFiles = [];

    // =========================
    // Word Counter
    // =========================

    textarea.addEventListener("input", () => {
        const words = textarea.value.trim() ? textarea.value.trim().split(/\s+/) : [];
        const count = words.length;
        const percentage = Math.min((count / MAX_WORDS) * 100, 100);

        wordCounter.textContent = `${count} / ${MAX_WORDS} words`;
        wordLimitFill.style.width = `${percentage}%`;

        // Update color classes
        wordCounter.classList.remove("warning", "danger");
        wordLimitFill.classList.remove("warning", "danger");

        if (count > MAX_WORDS) {
            wordCounter.classList.add("danger");
            wordLimitFill.classList.add("danger");
        } else if (count > MAX_WORDS * 0.8) {
            wordCounter.classList.add("warning");
            wordLimitFill.classList.add("warning");
        }

        updateSubmitButton();
    });

    // =========================
    // File Upload — Click
    // =========================

    uploadZone.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", (e) => {
        addFiles(Array.from(e.target.files));
        fileInput.value = ""; // Reset so same file can be re-selected
    });

    // =========================
    // File Upload — Drag & Drop
    // =========================

    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("dragover");
    });

    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("dragover");
    });

    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("dragover");
        const files = Array.from(e.dataTransfer.files).filter(f =>
            f.name.toLowerCase().endsWith(".pdf")
        );
        addFiles(files);
    });

    // =========================
    // File Management
    // =========================

    function addFiles(newFiles) {
        for (const file of newFiles) {
            if (selectedFiles.length >= MAX_FILES) break;
            // Avoid duplicates by name
            if (selectedFiles.some(f => f.name === file.name)) continue;
            if (!file.name.toLowerCase().endsWith(".pdf")) continue;
            selectedFiles.push(file);
        }
        renderFileList();
        updateSubmitButton();
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        renderFileList();
        updateSubmitButton();
    }

    function renderFileList() {
        fileList.innerHTML = "";
        fileCounter.textContent = `${selectedFiles.length} / ${MAX_FILES} files`;

        selectedFiles.forEach((file, index) => {
            const item = document.createElement("div");
            item.className = "file-item";
            item.style.animationDelay = `${index * 0.05}s`;
            item.innerHTML = `
                <span class="file-item-name">
                    📄 ${file.name}
                    <span style="color: var(--text-muted); font-size: 0.75rem;">
                        (${(file.size / 1024).toFixed(0)} KB)
                    </span>
                </span>
                <button type="button" class="file-item-remove" data-index="${index}" title="Remove file">✕</button>
            `;
            fileList.appendChild(item);
        });

        // Add remove handlers
        fileList.querySelectorAll(".file-item-remove").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                removeFile(parseInt(btn.dataset.index));
            });
        });
    }

    // =========================
    // Submit Button State
    // =========================

    function updateSubmitButton() {
        const words = textarea.value.trim() ? textarea.value.trim().split(/\s+/) : [];
        const hasValidJD = words.length > 0 && words.length <= MAX_WORDS;
        const hasFiles = selectedFiles.length > 0;
        submitBtn.disabled = !(hasValidJD && hasFiles);
    }

    // =========================
    // Form Submission
    // =========================

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();
        hideResults();

        // Show loading state
        const btnText = submitBtn.querySelector(".btn-text");
        const btnLoading = submitBtn.querySelector(".btn-loading");
        btnText.hidden = true;
        btnLoading.hidden = false;
        submitBtn.disabled = true;

        // Build FormData
        const formData = new FormData();
        formData.append("job_description", textarea.value.trim());
        for (const file of selectedFiles) {
            formData.append("resumes", file);
        }

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (data.status === "success") {
                renderResults(data);
            } else {
                showError(data.message || "An unexpected error occurred.");
            }
        } catch (err) {
            showError("Network error. Please check your connection and try again.");
        } finally {
            // Reset button state
            btnText.hidden = false;
            btnLoading.hidden = true;
            updateSubmitButton();
        }
    });

    // =========================
    // Error Display
    // =========================

    function showError(message) {
        errorMessage.textContent = "⚠️ " + message;
        errorContainer.hidden = false;
        errorContainer.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function hideError() {
        errorContainer.hidden = true;
    }

    // =========================
    // Results Rendering
    // =========================

    function hideResults() {
        resultsSection.hidden = true;
    }

    function renderResults(data) {
        resultsGrid.innerHTML = "";
        resultsCount.textContent = `${data.total_processed} resumes analyzed`;

        data.results.forEach((result, index) => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.style.animationDelay = `${index * 0.1}s`;

            const pct = result.match_percentage;
            const level = pct >= 70 ? "high" : pct >= 40 ? "medium" : "low";
            const rankClass = result.rank <= 3 ? `rank-${result.rank}` : "rank-default";

            // Matched skills badges
            const skillsHTML = result.matched_skills.length > 0
                ? result.matched_skills.map(s => `<span class="skill-badge">${s}</span>`).join("")
                : `<span class="no-skills">No matching skills found</span>`;

            // Missing skills badges (if any)
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

            card.innerHTML = `
                <div class="result-card-header">
                    <div class="result-rank">
                        <div class="rank-badge ${rankClass}">#${result.rank}</div>
                        <span class="result-filename">${result.candidate_filename || result.filename}</span>
                    </div>
                    <div class="result-percentage ${level}">${pct}%</div>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill ${level}" id="progress-${index}"></div>
                </div>
                
                <div class="skills-section">
                    ${skillsHTML}
                </div>

                <!-- Toggle details button -->
                <div class="detail-toggle-container">
                    <button class="detail-toggle-btn" id="toggle-btn-${index}">
                        <span>Diagnostics & Optimizer Plan</span>
                        <span class="arrow">▼</span>
                    </button>
                </div>

                <!-- Collapsible detail drawer -->
                <div class="detail-drawer" id="drawer-${index}" hidden>
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
            `;

            resultsGrid.appendChild(card);

            // Animate main progress bar after a short delay
            setTimeout(() => {
                const progressEl = document.getElementById(`progress-${index}`);
                if (progressEl) progressEl.style.width = `${pct}%`;
            }, 100 + index * 100);

            // Toggle collapsible details drawer
            const toggleBtn = card.querySelector(`#toggle-btn-${index}`);
            const drawer = card.querySelector(`#drawer-${index}`);
            toggleBtn.addEventListener("click", () => {
                const isHidden = drawer.hidden;
                drawer.hidden = !isHidden;
                toggleBtn.classList.toggle("expanded", isHidden);
            });
        });

        resultsSection.hidden = false;
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
});
