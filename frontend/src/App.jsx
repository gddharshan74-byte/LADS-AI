import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [summary, setSummary] = useState(null);
  const [highRiskProjects, setHighRiskProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);

  const [loading, setLoading] = useState(true);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectLoading, setProjectLoading] = useState(false);

  const [error, setError] = useState("");

  const investigationRef = useRef(null);

  // =========================================================
  // FETCH DASHBOARD SUMMARY
  // =========================================================

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/dashboard/summary`
        );

        setSummary(response.data);
      } catch (err) {
        console.error("Summary error:", err);

        setError(
          "Unable to connect to the LADS AI backend."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  // =========================================================
  // FETCH HIGH-RISK PROJECTS
  // =========================================================

  useEffect(() => {
    const fetchHighRiskProjects = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/projects/high-risk`
        );

        const data = response.data;

        console.log("High-risk projects:", data);

        if (Array.isArray(data)) {
          setHighRiskProjects(data);
        } else if (Array.isArray(data.projects)) {
          setHighRiskProjects(data.projects);
        } else if (
          Array.isArray(data.high_risk_projects)
        ) {
          setHighRiskProjects(data.high_risk_projects);
        } else {
          setHighRiskProjects([]);
        }
      } catch (err) {
        console.error(
          "High-risk projects error:",
          err
        );
      } finally {
        setProjectsLoading(false);
      }
    };

    fetchHighRiskProjects();
  }, []);

  // =========================================================
  // FETCH INDIVIDUAL PROJECT
  // =========================================================

  const openProject = async (projectId) => {
    try {
      setProjectLoading(true);
      setError("");

      const response = await axios.get(
        `${API_URL}/projects/${projectId}`
      );

      setSelectedProject(response.data);

      setTimeout(() => {
        investigationRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 180);
    } catch (err) {
      console.error(
        "Project details error:",
        err
      );

      setError(
        `Unable to load project ${projectId}.`
      );
    } finally {
      setProjectLoading(false);
    }
  };

  // =========================================================
  // DATA HELPERS
  // =========================================================

  const getProjectId = (project) =>
    project?.project_id ??
    project?.id ??
    project?.Project_ID ??
    "Unknown";

  const getRiskScore = (project) =>
    Number(
      project?.risk_score ??
        project?.score ??
        project?.Risk_Score ??
        0
    );

  const getRiskLevel = (project) =>
    project?.risk_level ??
    project?.risk ??
    project?.Risk_Level ??
    "High";

  const getWorkDescription = (project) =>
    project?.work_description ??
    project?.description ??
    project?.work_name ??
    project?.work ??
    project?.Work_Description ??
    "Project description unavailable";

  const getLocation = (project) => {
    const district =
      project?.district ??
      project?.District ??
      "";

    const state =
      project?.state ??
      project?.State ??
      "";

    if (district && state) {
      return `${district}, ${state}`;
    }

    return (
      district ||
      state ||
      project?.location ||
      project?.Location ||
      "Location unavailable"
    );
  };

  const getReasons = (project) => {
    if (!project) {
      return [
        "Multiple risk signals require review."
      ];
    }

    if (
      typeof project.risk_reasons === "string"
    ) {
      return project.risk_reasons
        .split("|")
        .map((reason) => reason.trim())
        .filter(Boolean);
    }

    if (Array.isArray(project.risk_reasons)) {
      return project.risk_reasons;
    }

    if (Array.isArray(project.reasons)) {
      return project.reasons;
    }

    if (Array.isArray(project.alerts)) {
      return project.alerts;
    }

    const reasons = [];

    if (
      project.cost_risk === "High" ||
      project.cost_anomaly === true
    ) {
      reasons.push("Potential cost anomaly");
    }

    if (
      project.delay_risk === "High" ||
      project.delay_anomaly === true
    ) {
      reasons.push("Potential execution delay");
    }

    if (
      project.duplicate_risk === "High" ||
      project.duplicate_anomaly === true
    ) {
      reasons.push(
        "Potentially similar or duplicate work"
      );
    }

    if (
      project.spending_risk === "High" ||
      project.spending_anomaly === true
    ) {
      reasons.push(
        "Unusual spending pattern"
      );
    }

    if (reasons.length === 0) {
      reasons.push(
        "Multiple risk signals require review."
      );
    }

    return reasons;
  };

  const formatNumber = (
    value,
    decimals = 2
  ) => {
    const number = Number(value);

    if (Number.isNaN(number)) {
      return "-";
    }

    return number.toFixed(decimals);
  };

  const formatPercent = (value) => {
    const number = Number(value);

    if (Number.isNaN(number)) {
      return "-";
    }

    return `${number.toFixed(2)}%`;
  };

  const getProgressWidth = (value) => {
    const number = Number(value);

    if (Number.isNaN(number)) {
      return 0;
    }

    return Math.max(
      0,
      Math.min(100, number)
    );
  };

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className="app">

      {/* ===================================================
          HEADER
      =================================================== */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            <span>L</span>
            <span>A</span>
          </div>

          <div>
            <h1>LADS AI</h1>

            <p>
              MPLADS Risk Intelligence Platform
            </p>
          </div>

        </div>

        <div className="topbar-right">

          <div className="system-status">
            <span className="status-dot"></span>

            <div>
              <strong>
                System Online
              </strong>

              <small>
                API Connected
              </small>
            </div>
          </div>

        </div>

      </header>

      <main className="dashboard">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="hero">

          <div className="hero-content">

            <div className="hero-badge">
              AI-POWERED MONITORING
            </div>

            <h2>
              Identify risks.
              <br />
              <span>
                Prioritize action.
              </span>
            </h2>

            <p>
              LADS AI analyzes MPLADS project,
              expenditure and implementation data
              to identify potential anomalies and
              prioritize cases for human review.
            </p>

            <div className="hero-flow">

              <span>DATA</span>
              <b>→</b>
              <span>AI ANALYSIS</span>
              <b>→</b>
              <span>RISK SCORE</span>
              <b>→</b>
              <span>HUMAN REVIEW</span>

            </div>

          </div>

          <div className="hero-orbit">

            <div className="orbit-ring ring-one"></div>
            <div className="orbit-ring ring-two"></div>

            <div className="orbit-core">
              <span>AI</span>
              <small>RISK<br />ENGINE</small>
            </div>

          </div>

        </section>

        {/* =================================================
            STATISTICS
        ================================================= */}

        <section className="stats">

          <div className="stat-card total">

            <div className="stat-top">
              <span>01</span>
              <small>PROJECTS</small>
            </div>

            <p>
              Projects Monitored
            </p>

            <strong>
              {loading
                ? "..."
                : summary?.total_projects ?? "-"}
            </strong>

            <div className="stat-footer">
              Demo dataset
            </div>

          </div>

          <div className="stat-card high">

            <div className="stat-top">
              <span>02</span>
              <small>PRIORITY</small>
            </div>

            <p>
              High Risk
            </p>

            <strong>
              {loading
                ? "..."
                : summary?.high_risk ?? "-"}
            </strong>

            <div className="stat-footer">
              Requires review
            </div>

          </div>

          <div className="stat-card medium">

            <div className="stat-top">
              <span>03</span>
              <small>ATTENTION</small>
            </div>

            <p>
              Medium Risk
            </p>

            <strong>
              {loading
                ? "..."
                : summary?.medium_risk ?? "-"}
            </strong>

            <div className="stat-footer">
              Monitor closely
            </div>

          </div>

          <div className="stat-card low">

            <div className="stat-top">
              <span>04</span>
              <small>ROUTINE</small>
            </div>

            <p>
              Low Risk
            </p>

            <strong>
              {loading
                ? "..."
                : summary?.low_risk ?? "-"}
            </strong>

            <div className="stat-footer">
              Routine monitoring
            </div>

          </div>

        </section>

        {/* =================================================
            ERROR
        ================================================= */}

        {error && (
          <div className="error-box">
            <strong>Connection issue</strong>
            <span>{error}</span>
          </div>
        )}

        {/* =================================================
            PIPELINE
        ================================================= */}

        <section className="pipeline-card">

          <div className="section-title-row">

            <div>

              <div className="mini-label">
                HOW IT WORKS
              </div>

              <h3>
                Risk Intelligence Pipeline
              </h3>

            </div>

            <div className="pipeline-tag">
              MULTI-SIGNAL ANALYSIS
            </div>

          </div>

          <div className="pipeline-track">

            <div className="pipeline-step active">

              <div className="pipeline-icon">
                01
              </div>

              <strong>
                MPLADS Data
              </strong>

              <span>
                Project records
              </span>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">

              <div className="pipeline-icon">
                02
              </div>

              <strong>
                AI Analysis
              </strong>

              <span>
                Detect signals
              </span>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">

              <div className="pipeline-icon">
                03
              </div>

              <strong>
                Risk Score
              </strong>

              <span>
                Prioritize cases
              </span>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">

              <div className="pipeline-icon">
                04
              </div>

              <strong>
                Explain
              </strong>

              <span>
                Show reasons
              </span>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step final">

              <div className="pipeline-icon">
                05
              </div>

              <strong>
                Human Review
              </strong>

              <span>
                Verify & act
              </span>

            </div>

          </div>

          <div className="signal-row">

            <span className="signal cost">
              COST
            </span>

            <span className="signal delay">
              DELAY
            </span>

            <span className="signal duplicate">
              DUPLICATE
            </span>

            <span className="signal spending">
              SPENDING
            </span>

          </div>

        </section>

        {/* =================================================
            HIGH-RISK QUEUE
        ================================================= */}

        <section className="projects-card">

          <div className="section-heading">

            <div>

              <div className="mini-label">
                PRIORITY QUEUE
              </div>

              <h3>
                High-Risk Projects
              </h3>

              <p>
                Projects prioritized for human
                review based on detected risk signals.
              </p>

            </div>

            <div className="priority-badge">
              AI PRIORITIZED
            </div>

          </div>

          {projectsLoading && (
            <div className="loading-box">
              Loading priority queue...
            </div>
          )}

          {!projectsLoading &&
            highRiskProjects.length === 0 && (
              <div className="loading-box">
                No high-risk projects available.
              </div>
            )}

          {!projectsLoading &&
            highRiskProjects.length > 0 && (

              <div className="project-list">

                {highRiskProjects.map(
                  (project, index) => {

                    const projectId =
                      getProjectId(project);

                    const score =
                      getRiskScore(project);

                    const level =
                      getRiskLevel(project);

                    return (

                      <div
                        className="project-row"
                        key={`${projectId}-${index}`}
                        role="button"
                        tabIndex={0}
                        onClick={() =>
                          openProject(projectId)
                        }
                        onKeyDown={(event) => {

                          if (
                            event.key === "Enter" ||
                            event.key === " "
                          ) {

                            event.preventDefault();

                            openProject(
                              projectId
                            );
                          }

                        }}
                      >

                        <div className="project-number">
                          {String(
                            index + 1
                          ).padStart(2, "0")}
                        </div>

                        <div className="project-main">

                          <div className="project-id">
                            {projectId}
                          </div>

                          <div className="project-description">
                            {getWorkDescription(
                              project
                            )}
                          </div>

                          <div className="project-location">
                            <span>●</span>
                            {getLocation(
                              project
                            )}
                          </div>

                        </div>

                        <div className="project-risk">

                          <div className="risk-score">

                            <strong>
                              {score.toFixed(2)}
                            </strong>

                            <span>
                              /100
                            </span>

                          </div>

                          <span
                            className={`risk-pill ${String(
                              level
                            ).toLowerCase()}`}
                          >
                            {level}
                          </span>

                        </div>

                        <button
                          className="investigate-button"
                          type="button"
                          onClick={(event) => {

                            event.stopPropagation();

                            openProject(
                              projectId
                            );

                          }}
                        >
                          Investigate
                          <span>→</span>
                        </button>

                      </div>

                    );
                  }
                )}

              </div>
            )}

        </section>

        {/* =================================================
            INVESTIGATION
        ================================================= */}

        {selectedProject && (

          <section
            ref={investigationRef}
            className="investigation-card"
          >

            <div className="investigation-header">

              <div>

                <div className="mini-label">
                  PROJECT INVESTIGATION
                </div>

                <h3>
                  {getProjectId(
                    selectedProject
                  )}
                </h3>

                <p>
                  AI-generated risk intelligence
                  for official review.
                </p>

              </div>

              <button
                className="close-button"
                type="button"
                onClick={() =>
                  setSelectedProject(null)
                }
              >
                Close ×
              </button>

            </div>

            {projectLoading && (

              <div className="loading-box">
                Loading project intelligence...
              </div>

            )}

            {!projectLoading && (

              <>

                {/* =======================================
                    INVESTIGATION HERO
                ======================================= */}

                <div className="investigation-hero">

                  <div className="investigation-project">

                    <span>
                      HIGH-PRIORITY CASE
                    </span>

                    <h4>
                      {getWorkDescription(
                        selectedProject
                      )}
                    </h4>

                    <p>
                      {getLocation(
                        selectedProject
                      )}
                    </p>

                  </div>

                  <div className="overall-risk">

                    <small>
                      OVERALL RISK
                    </small>

                    <strong>
                      {formatNumber(
                        getRiskScore(
                          selectedProject
                        )
                      )}
                    </strong>

                    <span>
                      / 100
                    </span>

                    <div className="overall-risk-label">
                      {getRiskLevel(
                        selectedProject
                      )}
                    </div>

                  </div>

                </div>

                {/* =======================================
                    RISK BREAKDOWN
                ======================================= */}

                <div className="investigation-section">

                  <div className="subsection-heading">

                    <div>

                      <div className="mini-label">
                        AI SIGNALS
                      </div>

                      <h4>
                        Risk Intelligence Breakdown
                      </h4>

                    </div>

                  </div>

                  <div className="risk-breakdown-grid">

                    <div className="risk-component cost-component">

                      <div className="component-heading">
                        <span className="component-dot"></span>
                        Cost Risk
                      </div>

                      <strong>
                        {formatNumber(
                          selectedProject.cost_score
                        )}
                      </strong>

                      <div className="risk-bar">
                        <div
                          style={{
                            width: `${getProgressWidth(
                              selectedProject.cost_score
                            )}%`,
                          }}
                        ></div>
                      </div>

                      <small>
                        Cost anomaly signal
                      </small>

                    </div>

                    <div className="risk-component delay-component">

                      <div className="component-heading">
                        <span className="component-dot"></span>
                        Delay Risk
                      </div>

                      <strong>
                        {formatNumber(
                          selectedProject.delay_score
                        )}
                      </strong>

                      <div className="risk-bar">
                        <div
                          style={{
                            width: `${getProgressWidth(
                              selectedProject.delay_score
                            )}%`,
                          }}
                        ></div>
                      </div>

                      <small>
                        Execution timeline signal
                      </small>

                    </div>

                    <div className="risk-component duplicate-component">

                      <div className="component-heading">
                        <span className="component-dot"></span>
                        Duplicate Risk
                      </div>

                      <strong>
                        {formatNumber(
                          selectedProject.duplicate_score
                        )}
                      </strong>

                      <div className="risk-bar">
                        <div
                          style={{
                            width: `${getProgressWidth(
                              selectedProject.duplicate_score
                            )}%`,
                          }}
                        ></div>
                      </div>

                      <small>
                        Text similarity signal
                      </small>

                    </div>

                    <div className="risk-component spending-component">

                      <div className="component-heading">
                        <span className="component-dot"></span>
                        Spending Risk
                      </div>

                      <strong>
                        {formatNumber(
                          selectedProject.spending_score
                        )}
                      </strong>

                      <div className="risk-bar">
                        <div
                          style={{
                            width: `${getProgressWidth(
                              selectedProject.spending_score
                            )}%`,
                          }}
                        ></div>
                      </div>

                      <small>
                        Spending pattern signal
                      </small>

                    </div>

                  </div>

                </div>

                {/* =======================================
                    FINANCIAL SNAPSHOT
                ======================================= */}

                <div className="investigation-section">

                  <div className="subsection-heading">

                    <div>

                      <div className="mini-label">
                        FINANCIAL ANALYSIS
                      </div>

                      <h4>
                        Financial Snapshot
                      </h4>

                    </div>

                  </div>

                  <div className="detail-grid">

                    <div className="detail-item">

                      <span>
                        Estimated Cost
                      </span>

                      <strong>
                        ₹
                        {formatNumber(
                          selectedProject
                            .estimated_cost_lakh
                        )} L
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Sanctioned Amount
                      </span>

                      <strong>
                        ₹
                        {formatNumber(
                          selectedProject
                            .sanctioned_amount_lakh
                        )} L
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Expenditure
                      </span>

                      <strong>
                        ₹
                        {formatNumber(
                          selectedProject
                            .expenditure_lakh
                        )} L
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Cost Overrun
                      </span>

                      <strong className="danger-value">
                        {formatPercent(
                          selectedProject
                            .sanction_overrun_pct
                        )}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =======================================
                    EXECUTION
                ======================================= */}

                <div className="investigation-section">

                  <div className="subsection-heading">

                    <div>

                      <div className="mini-label">
                        EXECUTION ANALYSIS
                      </div>

                      <h4>
                        Project Progress
                      </h4>

                    </div>

                  </div>

                  <div className="detail-grid">

                    <div className="detail-item">

                      <span>
                        Physical Progress
                      </span>

                      <strong>
                        {formatPercent(
                          selectedProject
                            .physical_progress_pct
                        )}
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Current Status
                      </span>

                      <strong className="danger-value">
                        {selectedProject
                          .current_status ?? "-"}
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Delay
                      </span>

                      <strong>
                        {selectedProject.delay_days ??
                          "-"} days
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Delay vs Plan
                      </span>

                      <strong className="danger-value">
                        {formatPercent(
                          selectedProject.delay_pct
                        )}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =======================================
                    TEXT ANALYSIS
                ======================================= */}

                <div className="investigation-section">

                  <div className="subsection-heading">

                    <div>

                      <div className="mini-label">
                        TEXT ANALYSIS
                      </div>

                      <h4>
                        Similarity Check
                      </h4>

                    </div>

                  </div>

                  <div className="similarity-box">

                    <div className="similarity-stat">

                      <span>
                        Maximum Similarity
                      </span>

                      <strong>
                        {formatPercent(
                          selectedProject
                            .max_similarity_pct
                        )}
                      </strong>

                    </div>

                    <div className="similarity-stat">

                      <span>
                        Similar Projects
                      </span>

                      <strong>
                        {selectedProject
                          .similar_project_count ??
                          "-"}
                      </strong>

                    </div>

                    <div className="similarity-stat">

                      <span>
                        Similarity Signal
                      </span>

                      <strong>
                        {formatNumber(
                          selectedProject
                            .duplicate_score
                        )}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =======================================
                    WHY FLAGGED
                ======================================= */}

                <div className="alert-section">

                  <div className="alert-header">

                    <div className="alert-symbol">
                      !
                    </div>

                    <div>

                      <div className="mini-label">
                        EXPLAINABLE ALERT
                      </div>

                      <h4>
                        Why was this project flagged?
                      </h4>

                      <p>
                        These signals contributed to
                        the project's risk assessment.
                      </p>

                    </div>

                  </div>

                  <div className="reason-list">

                    {getReasons(
                      selectedProject
                    ).map(
                      (reason, index) => (

                        <div
                          className="reason-item"
                          key={index}
                        >

                          <span>
                            {String(
                              index + 1
                            ).padStart(2, "0")}
                          </span>

                          <p>
                            {String(reason)}
                          </p>

                        </div>

                      )
                    )}

                  </div>

                </div>

                {/* =======================================
                    HUMAN REVIEW
                ======================================= */}

                <div className="review-banner">

                  <div className="review-icon">
                    ✓
                  </div>

                  <div className="review-content">

                    <div className="mini-label">
                      RECOMMENDED ACTION
                    </div>

                    <h4>
                      Human Review Required
                    </h4>

                    <p>
                      LADS AI identifies potential
                      anomalies and prioritizes cases.
                      Final verification and action
                      remain with authorized officials.
                    </p>

                  </div>

                  <div className="review-arrow">
                    →
                  </div>

                </div>

              </>

            )}

          </section>

        )}

        {/* =================================================
            FOOTER
        ================================================= */}

        <footer className="footer">

          <span>
            LADS AI · MPLADS Risk Intelligence
          </span>

          <span>
            AI-assisted monitoring ·
            Human decision remains final
          </span>

        </footer>

      </main>

    </div>
  );
}

export default App;