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
  // DASHBOARD SUMMARY
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
  // HIGH-RISK PROJECTS
  // =========================================================

  useEffect(() => {
    const fetchHighRiskProjects = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/projects/high-risk`
        );

        const data = response.data;

        console.log(
          "High-risk projects:",
          data
        );

        if (Array.isArray(data)) {
          setHighRiskProjects(data);
        } else if (Array.isArray(data.projects)) {
          setHighRiskProjects(data.projects);
        } else if (
          Array.isArray(data.high_risk_projects)
        ) {
          setHighRiskProjects(
            data.high_risk_projects
          );
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
  // INDIVIDUAL PROJECT
  // =========================================================

  const openProject = async (projectId) => {
    try {
      setProjectLoading(true);
      setError("");

      const response = await axios.get(
        `${API_URL}/projects/${projectId}`
      );

      console.log(
        "Project details:",
        response.data
      );

      setSelectedProject(response.data);

      setTimeout(() => {
        investigationRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 200);

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
    project?.risk_score ??
    project?.score ??
    project?.Risk_Score ??
    0;

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

    // Backend currently returns risk_reasons
    // as one string separated by "|".
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
      reasons.push(
        "Potential cost anomaly"
      );
    }

    if (
      project.delay_risk === "High" ||
      project.delay_anomaly === true
    ) {
      reasons.push(
        "Potential execution delay"
      );
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

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* ===================================================
          HEADER
      =================================================== */}

      <header className="header">

        <div className="brand">
          <h1>LADS AI</h1>
          <p>MPLADS Risk Intelligence</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Connected
        </div>

      </header>

      {/* ===================================================
          MAIN DASHBOARD
      =================================================== */}

      <main className="dashboard">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="hero">

          <p className="eyebrow">
            AI-POWERED PROJECT MONITORING
          </p>

          <h2>
            Identify risks.
            <br />
            Prioritize action.
          </h2>

          <p className="hero-text">
            LADS AI analyzes MPLADS project data to
            identify potential cost, delay, spending,
            and duplication anomalies.
          </p>

        </section>

        {/* =================================================
            STATS
        ================================================= */}

        <section className="stats">

          <div className="stat-card">

            <span>
              Total Projects
            </span>

            <strong>
              {loading
                ? "..."
                : summary?.total_projects ?? "-"}
            </strong>

          </div>

          <div className="stat-card high">

            <span>
              High Risk
            </span>

            <strong>
              {loading
                ? "..."
                : summary?.high_risk ?? "-"}
            </strong>

          </div>

          <div className="stat-card medium">

            <span>
              Medium Risk
            </span>

            <strong>
              {loading
                ? "..."
                : summary?.medium_risk ?? "-"}
            </strong>

          </div>

          <div className="stat-card low">

            <span>
              Low Risk
            </span>

            <strong>
              {loading
                ? "..."
                : summary?.low_risk ?? "-"}
            </strong>

          </div>

        </section>

        {/* =================================================
            ERROR
        ================================================= */}

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        {/* =================================================
            PIPELINE
        ================================================= */}

        <section className="info-card">

          <div className="info-heading">

            <p className="section-eyebrow">
              RISK INTELLIGENCE
            </p>

            <h3>
              Risk Intelligence Pipeline
            </h3>

            <p>
              MPLADS Data → AI Analysis → Risk Score →
              Explainable Alert → Human Review
            </p>

          </div>

          <div className="pipeline">

            <span>Cost</span>
            <span>Delay</span>
            <span>Duplicate</span>
            <span>Spending</span>

          </div>

        </section>

        {/* =================================================
            HIGH-RISK PROJECTS
        ================================================= */}

        <section className="projects-card">

          <div className="section-heading">

            <div>

              <p className="section-eyebrow">
                PRIORITY QUEUE
              </p>

              <h3>
                High-Risk Projects
              </h3>

              <p>
                Projects prioritized for human review
                based on detected risk signals.
              </p>

            </div>

            <div className="priority-badge">
              AI PRIORITIZED
            </div>

          </div>

          {projectsLoading && (
            <div className="loading-box">
              Loading high-risk projects...
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
                      Number(
                        getRiskScore(project)
                      );

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
                              / 100
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
                          Investigate →
                        </button>

                      </div>

                    );
                  }
                )}

              </div>
            )}

        </section>

        {/* =================================================
            PROJECT INVESTIGATION
        ================================================= */}

        {selectedProject && (

          <section
            ref={investigationRef}
            className="investigation-card"
          >

            {/* Header */}

            <div className="investigation-header">

              <div>

                <p className="section-eyebrow">
                  PROJECT INVESTIGATION
                </p>

                <h3>
                  Project{" "}
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
                Close
              </button>

            </div>

            {projectLoading && (
              <div className="loading-box">
                Loading project intelligence...
              </div>
            )}

            {!projectLoading && (

              <>

                {/* =========================================
                    TOP RISK SUMMARY
                ========================================= */}

                <div className="investigation-summary">

                  <div className="big-risk-score">

                    <span>
                      RISK SCORE
                    </span>

                    <div>

                      <strong>
                        {formatNumber(
                          getRiskScore(
                            selectedProject
                          ),
                          2
                        )}
                      </strong>

                      <small>
                        / 100
                      </small>

                    </div>

                  </div>

                  <div className="risk-status-box">

                    <span>
                      RISK LEVEL
                    </span>

                    <strong>
                      {getRiskLevel(
                        selectedProject
                      )}
                    </strong>

                    <p>
                      Potential anomaly requiring
                      human review.
                    </p>

                  </div>

                </div>

                {/* =========================================
                    RISK BREAKDOWN
                ========================================= */}

                <div className="investigation-section">

                  <div className="subsection-header">

                    <div>

                      <p className="section-eyebrow">
                        AI SIGNALS
                      </p>

                      <h4>
                        Risk Intelligence Breakdown
                      </h4>

                    </div>

                  </div>

                  <div className="risk-breakdown-grid">

                    <div className="risk-component cost-component">

                      <span>
                        Cost Risk
                      </span>

                      <strong>
                        {formatNumber(
                          selectedProject.cost_score
                        )}
                      </strong>

                      <small>
                        Cost anomaly signal
                      </small>

                    </div>

                    <div className="risk-component delay-component">

                      <span>
                        Delay Risk
                      </span>

                      <strong>
                        {formatNumber(
                          selectedProject.delay_score
                        )}
                      </strong>

                      <small>
                        Execution timeline signal
                      </small>

                    </div>

                    <div className="risk-component duplicate-component">

                      <span>
                        Duplicate Risk
                      </span>

                      <strong>
                        {formatNumber(
                          selectedProject.duplicate_score
                        )}
                      </strong>

                      <small>
                        Text similarity signal
                      </small>

                    </div>

                    <div className="risk-component spending-component">

                      <span>
                        Spending Risk
                      </span>

                      <strong>
                        {formatNumber(
                          selectedProject.spending_score
                        )}
                      </strong>

                      <small>
                        Spending pattern signal
                      </small>

                    </div>

                  </div>

                </div>

                {/* =========================================
                    FINANCIAL SNAPSHOT
                ========================================= */}

                <div className="investigation-section">

                  <div className="subsection-header">

                    <div>

                      <p className="section-eyebrow">
                        FINANCIAL ANALYSIS
                      </p>

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
                        )} Lakh
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
                        )} Lakh
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
                        )} Lakh
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Sanction Overrun
                      </span>

                      <strong>
                        {formatPercent(
                          selectedProject
                            .sanction_overrun_pct
                        )}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =========================================
                    EXECUTION
                ========================================= */}

                <div className="investigation-section">

                  <div className="subsection-header">

                    <div>

                      <p className="section-eyebrow">
                        EXECUTION ANALYSIS
                      </p>

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
                        Status
                      </span>

                      <strong>
                        {selectedProject
                          .current_status ?? "-"}
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Delay
                      </span>

                      <strong>
                        {selectedProject.delay_days ?? "-"} days
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Delay vs Plan
                      </span>

                      <strong>
                        {formatPercent(
                          selectedProject.delay_pct
                        )}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =========================================
                    DUPLICATE ANALYSIS
                ========================================= */}

                <div className="investigation-section">

                  <div className="subsection-header">

                    <div>

                      <p className="section-eyebrow">
                        TEXT ANALYSIS
                      </p>

                      <h4>
                        Similarity Check
                      </h4>

                    </div>

                  </div>

                  <div className="detail-grid">

                    <div className="detail-item">

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

                    <div className="detail-item">

                      <span>
                        Similar Projects
                      </span>

                      <strong>
                        {selectedProject
                          .similar_project_count ?? "-"}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =========================================
                    OTHER PROJECT INFORMATION
                ========================================= */}

                <div className="investigation-section">

                  <div className="subsection-header">

                    <div>

                      <p className="section-eyebrow">
                        PROJECT CONTEXT
                      </p>

                      <h4>
                        Project Information
                      </h4>

                    </div>

                  </div>

                  <div className="detail-grid">

                    <div className="detail-item">

                      <span>
                        Project ID
                      </span>

                      <strong>
                        {getProjectId(
                          selectedProject
                        )}
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        MP Name
                      </span>

                      <strong>
                        {selectedProject
                          .mp_name ?? "-"}
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        Category
                      </span>

                      <strong>
                        {selectedProject
                          .category ?? "-"}
                      </strong>

                    </div>

                    <div className="detail-item">

                      <span>
                        District
                      </span>

                      <strong>
                        {selectedProject
                          .district ?? "-"}
                      </strong>

                    </div>

                    <div className="detail-item wide">

                      <span>
                        Work Description
                      </span>

                      <strong>
                        {getWorkDescription(
                          selectedProject
                        )}
                      </strong>

                    </div>

                    <div className="detail-item wide">

                      <span>
                        Implementing Agency
                      </span>

                      <strong>
                        {selectedProject
                          .implementing_agency ?? "-"}
                      </strong>

                    </div>

                  </div>

                </div>

                {/* =========================================
                    WHY FLAGGED
                ========================================= */}

                <div className="alert-section">

                  <div className="alert-title">

                    <span className="alert-icon">
                      !
                    </span>

                    <div>

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
                            •
                          </span>

                          <p>
                            {String(reason)}
                          </p>

                        </div>

                      )
                    )}

                  </div>

                </div>

                {/* =========================================
                    ACTION
                ========================================= */}

                <div className="review-banner">

                  <div>

                    <span>
                      RECOMMENDED ACTION
                    </span>

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

      </main>

    </div>
  );
}

export default App;