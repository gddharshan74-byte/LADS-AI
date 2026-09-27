import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import axios from "axios";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

function App() {
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  const [selectedProject, setSelectedProject] = useState(null);
  const [comparables, setComparables] = useState([]);

  const [loading, setLoading] = useState(true);
  const [projectLoading, setProjectLoading] = useState(false);
  const [comparablesLoading, setComparablesLoading] =
    useState(false);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [searchCategory, setSearchCategory] =
    useState("All Categories");

  const [riskFilter, setRiskFilter] =
    useState("All");

  const [stateFilter, setStateFilter] =
    useState("All States");

  const [statusFilter, setStatusFilter] =
    useState("All Status");

  const [lastUpdated, setLastUpdated] =
    useState(null);

  const [analysisRunning, setAnalysisRunning] =
    useState(false);

  const [analysisStep, setAnalysisStep] =
    useState(0);

  const investigationRef = useRef(null);

  // ============================================================
  // HELPERS
  // ============================================================

  const projectId = (p) =>
    p?.project_id ??
    p?.id ??
    p?.Project_ID ??
    "Unknown";

  const riskScore = (p) =>
    Number(
      p?.risk_score ??
        p?.score ??
        p?.Risk_Score ??
        0
    );

  const riskLevel = (p) =>
    p?.risk_level ??
    p?.risk ??
    p?.Risk_Level ??
    "Low";

  const category = (p) =>
    p?.category ??
    p?.Category ??
    "Unknown";

  const state = (p) =>
    p?.state ??
    p?.State ??
    "Unknown";

  const district = (p) =>
    p?.district ??
    p?.District ??
    "Unknown";

  const description = (p) =>
    p?.work_description ??
    p?.description ??
    p?.work_name ??
    p?.work ??
    p?.Work_Description ??
    "Project description unavailable";

  const status = (p) =>
    p?.current_status ??
    p?.status ??
    "Unknown";

  const mlScore = (p) =>
    Number(
      p?.isolation_anomaly_score ??
        p?.ml_anomaly_score ??
        0
    );

  const mlFlagged = (p) =>
    p?.isolation_flag === true ||
    p?.isolation_flag === "True" ||
    p?.isolation_flag === 1 ||
    p?.isolation_flag === "1";

  const formatNumber = (
    value,
    digits = 2
  ) => {
    const n = Number(value);

    return Number.isNaN(n)
      ? "-"
      : n.toFixed(digits);
  };

  const formatPercent = (value) => {
    const n = Number(value);

    return Number.isNaN(n)
      ? "-"
      : `${n.toFixed(1)}%`;
  };

  const clamp = (value) =>
    Math.max(
      0,
      Math.min(
        100,
        Number(value) || 0
      )
    );

  const reasons = (p) => {
    if (!p) {
      return [
        "Multiple risk signals require contextual review.",
      ];
    }

    if (typeof p.risk_reasons === "string") {
      return p.risk_reasons
        .split("|")
        .map((x) => x.trim())
        .filter(Boolean);
    }

    if (Array.isArray(p.risk_reasons)) {
      return p.risk_reasons;
    }

    const result = [];

    if (
      Number(p.cost_score ?? 0) > 0
    ) {
      result.push(
        `Cost overrun of ${formatPercent(
          p.sanction_overrun_pct
        )} above sanctioned amount`
      );
    }

    if (
      Number(p.delay_score ?? 0) > 0
    ) {
      result.push(
        `Project duration exceeds plan by ${formatPercent(
          p.delay_pct
        )}`
      );
    }

    if (
      Number(p.duplicate_score ?? 0) > 0
    ) {
      result.push(
        `Similar work description detected at ${formatPercent(
          p.max_similarity_pct
        )} similarity`
      );
    }

    if (
      Number(p.spending_score ?? 0) > 0
    ) {
      result.push(
        `Unusual expenditure pattern with z-score ${formatNumber(
          p.spending_zscore
        )}`
      );
    }

    return result.length
      ? result
      : [
          "Project requires contextual review.",
        ];
  };

  // ============================================================
  // ANALYSIS ANIMATION
  // ============================================================

  const runAnalysisAnimation = () => {
    setAnalysisRunning(true);
    setAnalysisStep(0);

    const steps = [
      900,
      1800,
      2700,
      3600,
      4500,
    ];

    steps.forEach((delay, index) => {
      window.setTimeout(() => {
        setAnalysisStep(index + 1);
      }, delay);
    });

    window.setTimeout(() => {
      setAnalysisRunning(false);
    }, 5400);
  };

  // ============================================================
  // FETCH DASHBOARD
  // ============================================================

  const fetchDashboard = useCallback(
    async () => {
      setLoading(true);
      setError("");

      try {
        const [
          summaryRes,
          projectsRes,
          analyticsRes,
        ] = await Promise.all([
          axios.get(
            `${API_URL}/dashboard/summary`
          ),
          axios.get(
            `${API_URL}/projects?limit=500`
          ),
          axios.get(
            `${API_URL}/dashboard/analytics`
          ),
        ]);

        setSummary(summaryRes.data);
        setAnalytics(analyticsRes.data);

        const data = projectsRes.data;

        const list = Array.isArray(data)
          ? data
          : data?.projects ??
            data?.data ??
            [];

        setProjects(
          Array.isArray(list)
            ? list
            : []
        );

        setLastUpdated(new Date());
      } catch (err) {
        console.error(err);

        setError(
          "Unable to connect to the PRISM AI backend."
        );
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // ============================================================
  // OPEN PROJECT
  // ============================================================

  const openProject = async (id) => {
    setProjectLoading(true);
    setComparablesLoading(true);
    setError("");

    try {
      const [
        projectRes,
        comparableRes,
      ] = await Promise.all([
        axios.get(
          `${API_URL}/projects/${id}`
        ),

        axios.get(
          `${API_URL}/projects/${id}/comparables`
        ),
      ]);

      setSelectedProject(
        projectRes.data
      );

      runAnalysisAnimation();

      const comparableData =
        comparableRes.data;

      setComparables(
        Array.isArray(comparableData)
          ? comparableData
          : comparableData?.comparables ??
              []
      );

      setTimeout(() => {
        investigationRef.current?.scrollIntoView(
          {
            behavior: "smooth",
            block: "start",
          }
        );
      }, 5500);
    } catch (err) {
      console.error(err);

      setError(
        `Unable to load project ${id}.`
      );
    } finally {
      setProjectLoading(false);
      setComparablesLoading(false);
    }
  };

  // ============================================================
  // FILTER OPTIONS
  // ============================================================

  const categories = useMemo(
    () =>
      [
        ...new Set(
          projects.map(category)
        ),
      ]
        .filter(Boolean)
        .sort(),
    [projects]
  );

  const states = useMemo(
    () =>
      [
        ...new Set(
          projects.map(state)
        ),
      ]
        .filter(Boolean)
        .sort(),
    [projects]
  );

  const statuses = useMemo(
    () =>
      [
        ...new Set(
          projects.map(status)
        ),
      ]
        .filter(Boolean)
        .sort(),
    [projects]
  );

  // ============================================================
  // FILTERED PROJECTS
  // ============================================================

  const filteredProjects = useMemo(() => {
    const q = search
      .trim()
      .toLowerCase();

    return projects.filter((p) => {
      const matchesSearch =
        !q ||
        `${projectId(p)}
         ${description(p)}
         ${district(p)}
         ${state(p)}
         ${category(p)}
         ${status(p)}`
          .toLowerCase()
          .includes(q);

      const matchesCategory =
        searchCategory ===
          "All Categories" ||
        category(p) ===
          searchCategory;

      const matchesRisk =
        riskFilter === "All" ||
        riskLevel(p) === riskFilter;

      const matchesState =
        stateFilter === "All States" ||
        state(p) === stateFilter;

      const matchesStatus =
        statusFilter === "All Status" ||
        status(p) === statusFilter;

      return (
        matchesSearch &&
        matchesCategory &&
        matchesRisk &&
        matchesState &&
        matchesStatus
      );
    });
  }, [
    projects,
    search,
    searchCategory,
    riskFilter,
    stateFilter,
    statusFilter,
  ]);

  // ============================================================
  // DASHBOARD COUNTS
  // ============================================================

  const total =
    summary?.total_projects ??
    projects.length;

  const high =
    summary?.high_risk_projects ??
    projects.filter(
      (p) => riskLevel(p) === "High"
    ).length;

  const medium =
    summary?.medium_risk_projects ??
    projects.filter(
      (p) =>
        riskLevel(p) === "Medium"
    ).length;

  const low =
    summary?.low_risk_projects ??
    projects.filter(
      (p) =>
        riskLevel(p) === "Low"
    ).length;

  const mlCount = projects.filter(
    mlFlagged
  ).length;

  const averageRisk =
    analytics?.average_risk_score ??
    projects.reduce(
      (sum, p) =>
        sum + riskScore(p),
      0
    ) / Math.max(projects.length, 1);

  const completedCount =
    projects.filter(
      (p) =>
        status(p) === "Completed"
    ).length;

  const inProgressCount =
    projects.filter(
      (p) =>
        status(p) === "In Progress"
    ).length;

  const delayedCount =
    projects.filter(
      (p) =>
        status(p) === "Delayed"
    ).length;

  const spendingSignals =
    projects.filter(
      (p) =>
        Number(
          p.spending_score ?? 0
        ) > 0
    ).length;

  const duplicateSignals =
    projects.filter(
      (p) =>
        Number(
          p.duplicate_score ?? 0
        ) > 0
    ).length;

  const delaySignals =
    projects.filter(
      (p) =>
        Number(
          p.delay_score ?? 0
        ) > 0
    ).length;

  const costSignals =
    projects.filter(
      (p) =>
        Number(
          p.cost_score ?? 0
        ) > 0
    ).length;

  // ============================================================
  // QUICK SEARCH
  // ============================================================

  const quickSearch = (value) => {
    setSearch(value);

    document
      .getElementById(
        "priority-section"
      )
      ?.scrollIntoView({
        behavior: "smooth",
      });
  };

  return (
    <div className="app">

      {/* ======================================================
          UTILITY BAR
      ====================================================== */}

      <div className="utility-bar">
        <div className="portal-width utility-inner">
          <div>
            Government Risk Intelligence Prototype
          </div>

          <div>
            MPLADS · Public Fund Monitoring
          </div>
        </div>
      </div>

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="main-header">

        <div className="portal-width header-inner">

          <div className="portal-brand">

            <button
              className="prism-emblem"
              onClick={() =>
                window.scrollTo({
                  top: 0,
                  behavior: "smooth",
                })
              }
            >
              <span>P</span>
              <span>R</span>
            </button>

            <div>
              <div className="prism-title">
                PRISM AI
              </div>

              <div className="prism-subtitle">
                MPLADS Risk Intelligence System
              </div>
            </div>

          </div>

          <div className="header-tools">

            <span className="prototype-badge">
              <i></i>
              Synthetic Prototype Data
            </span>

            <button
              className="header-refresh"
              onClick={fetchDashboard}
              disabled={loading}
            >
              ↻ Refresh
            </button>

            <div className="online-indicator">

              <span></span>

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

        </div>

      </header>

      {/* ======================================================
          NAVIGATION
      ====================================================== */}

      <nav className="portal-nav">

        <div className="portal-width nav-inner">

          <div className="nav-menu">

            <button className="active">
              Home
            </button>

            <button
              onClick={() =>
                document
                  .getElementById(
                    "priority-section"
                  )
                  ?.scrollIntoView({
                    behavior: "smooth",
                  })
              }
            >
              Priority Projects
            </button>

            <button
              onClick={() =>
                document
                  .getElementById(
                    "analytics-section"
                  )
                  ?.scrollIntoView({
                    behavior: "smooth",
                  })
              }
            >
              Risk Analytics
            </button>

            <button
              onClick={() => {
                if (selectedProject) {
                  investigationRef.current?.scrollIntoView(
                    {
                      behavior:
                        "smooth",
                    }
                  );
                }
              }}
            >
              Investigation
            </button>

          </div>

          <div className="nav-date">
            Last updated{" "}
            <strong>
              {lastUpdated
                ? lastUpdated.toLocaleTimeString(
                    [],
                    {
                      hour: "2-digit",
                      minute: "2-digit",
                    }
                  )
                : "—"}
            </strong>
          </div>

        </div>

      </nav>

      {/* ======================================================
          HERO
      ====================================================== */}

      <section className="portal-hero">

        <div className="hero-overlay"></div>

        <div className="portal-width hero-content">

          <div className="hero-branding">

            <div className="hero-kicker">
              PRISM AI
            </div>

            <h1>
              MPLADS Risk Intelligence
            </h1>

            <p>
              Identify unusual patterns,
              prioritize high-risk projects
              and help officials focus review
              where attention matters most.
            </p>

          </div>

          <div className="portal-search">

            <div className="search-input-wrap">

              <span className="search-symbol">
                ⌕
              </span>

              <input
                value={search}
                onChange={(e) =>
                  setSearch(
                    e.target.value
                  )
                }
                placeholder="Search project ID, district, work description, category..."
              />

            </div>

            <select
              value={searchCategory}
              onChange={(e) =>
                setSearchCategory(
                  e.target.value
                )
              }
            >
              <option>
                All Categories
              </option>

              {categories.map(
                (item) => (
                  <option
                    key={item}
                    value={item}
                  >
                    {item}
                  </option>
                )
              )}

            </select>

            <button
              onClick={() =>
                document
                  .getElementById(
                    "priority-section"
                  )
                  ?.scrollIntoView({
                    behavior:
                      "smooth",
                  })
              }
            >
              Search
            </button>

          </div>

          <div className="quick-search">

            <span>
              Quick Search:
            </span>

            <button
              onClick={() => {
                setRiskFilter("High");
                setSearch("");
                quickSearch("");
              }}
            >
              High Risk Projects
            </button>

            <button
              onClick={() => {
                setRiskFilter("All");
                setSearch("");
                quickSearch("");
              }}
            >
              ML Anomalies
            </button>

            <button
              onClick={() => {
                setStatusFilter("Delayed");
                setSearch("");
                quickSearch("");
              }}
            >
              Delayed Projects
            </button>

            <button
              onClick={() => {
                setSearch("Community");
                setRiskFilter("All");
                quickSearch("Community");
              }}
            >
              Community Works
            </button>

            <button
              onClick={() => {
                setStateFilter(
                  states[0] ??
                    "All States"
                );
                setSearch("");
                quickSearch("");
              }}
            >
              State-wise Review
            </button>

          </div>

        </div>

      </section>

      {/* ======================================================
          KPI STRIP
      ====================================================== */}

      <section className="portal-width stat-strip">

        <PortalStat
          icon="▦"
          value={
            loading
              ? "—"
              : total
          }
          label="Projects Monitored"
          tone="blue"
        />

        <PortalStat
          icon="!"
          value={
            loading
              ? "—"
              : high
          }
          label="High Risk"
          tone="red"
        />

        <PortalStat
          icon="!"
          value={
            loading
              ? "—"
              : medium
          }
          label="Medium Risk"
          tone="amber"
        />

        <PortalStat
          icon="✓"
          value={
            loading
              ? "—"
              : low
          }
          label="Low Risk"
          tone="green"
        />

        <PortalStat
          icon="AI"
          value={
            loading
              ? "—"
              : mlCount
          }
          label="ML Anomalies"
          tone="purple"
        />

        <PortalStat
          icon="◈"
          value={
            loading
              ? "—"
              : formatNumber(
                  averageRisk
                )
          }
          label="Average Risk"
          tone="blue"
        />

      </section>

      {/* ======================================================
          RISK INTELLIGENCE
      ====================================================== */}

      <section className="portal-width section-block">

        <div className="section-title-row">

          <div>
            <span>
              RISK INTELLIGENCE
            </span>

            <h2>
              From project records
              to actionable insight
            </h2>
          </div>

          <p>
            PRISM AI combines transparent
            rule-based checks with an
            independent ML anomaly signal.
          </p>

        </div>

        <div className="red-feature-layout">

          <div className="red-feature-main">

            <div className="red-feature-label">
              PRIORITY MONITORING
            </div>

            <h3>
              Which projects
              deserve attention first?
            </h3>

            <p>
              PRISM AI screens project
              records across financial,
              temporal, textual and
              spending signals before
              sending cases to human
              review.
            </p>

            <button
              onClick={() =>
                document
                  .getElementById(
                    "priority-section"
                  )
                  ?.scrollIntoView({
                    behavior:
                      "smooth",
                  })
              }
            >
              View Priority Queue →
            </button>

          </div>

          <div className="red-feature-stats">

            <div>
              <strong>
                {high}
              </strong>

              <span>
                High risk
              </span>
            </div>

            <div>
              <strong>
                {mlCount}
              </strong>

              <span>
                ML anomaly signals
              </span>
            </div>

            <div>
              <strong>
                4
              </strong>

              <span>
                Core explainable signals
              </span>
            </div>

          </div>

        </div>

      </section>

      {/* ======================================================
          RISK ANALYTICS
      ====================================================== */}

      <section
        id="analytics-section"
        className="portal-width section-block"
      >

        <div className="section-title-row">

          <div>
            <span>
              RISK ANALYTICS
            </span>

            <h2>
              Project Risk Overview
            </h2>
          </div>

          <p>
            A visual summary of risk levels,
            implementation status and the
            anomaly signals driving review
            priority.
          </p>

        </div>

        <div className="analytics-dashboard">

          {/* RISK DISTRIBUTION */}

          <div className="analytics-panel">

            <div className="analytics-panel-header">

              <div>
                <span>
                  RISK DISTRIBUTION
                </span>

                <h3>
                  Projects by risk level
                </h3>
              </div>

              <div className="analytics-total">

                {total}

                <small>
                  projects
                </small>

              </div>

            </div>

            <div className="risk-chart">

              <div className="risk-chart-legend">

                <div className="legend-row">

                  <span className="legend-dot high"></span>

                  <div>
                    <strong>
                      High Risk
                    </strong>

                    <small>
                      Immediate review
                    </small>
                  </div>

                  <b>
                    {high}
                  </b>

                </div>

                <div className="legend-row">

                  <span className="legend-dot medium"></span>

                  <div>
                    <strong>
                      Medium Risk
                    </strong>

                    <small>
                      Requires attention
                    </small>
                  </div>

                  <b>
                    {medium}
                  </b>

                </div>

                <div className="legend-row">

                  <span className="legend-dot low"></span>

                  <div>
                    <strong>
                      Low Risk
                    </strong>

                    <small>
                      Routine monitoring
                    </small>
                  </div>

                  <b>
                    {low}
                  </b>

                </div>

              </div>

              <div className="horizontal-bars">

                <ChartBar
                  label="High"
                  value={high}
                  total={total}
                  tone="high"
                />

                <ChartBar
                  label="Medium"
                  value={medium}
                  total={total}
                  tone="medium"
                />

                <ChartBar
                  label="Low"
                  value={low}
                  total={total}
                  tone="low"
                />

              </div>

            </div>

          </div>

          {/* PROJECT STATUS */}

          <div className="analytics-panel">

            <div className="analytics-panel-header">

              <div>
                <span>
                  IMPLEMENTATION STATUS
                </span>

                <h3>
                  Current project status
                </h3>
              </div>

            </div>

            <div className="status-visual">

              <div
                className="status-donut"
                style={{
                  "--completed": `${
                    projects.length
                      ? (
                          (completedCount /
                            projects.length) *
                          100
                        ).toFixed(2)
                      : 0
                  }%`,

                  "--progress": `${
                    projects.length
                      ? (
                          (inProgressCount /
                            projects.length) *
                          100
                        ).toFixed(2)
                      : 0
                  }%`,
                }}
              >

                <div>

                  <strong>
                    {projects.length}
                  </strong>

                  <span>
                    Projects
                  </span>

                </div>

              </div>

              <div className="status-list">

                <StatusItem
                  label="Completed"
                  value={completedCount}
                  note="Execution finished"
                  tone="completed"
                />

                <StatusItem
                  label="In Progress"
                  value={inProgressCount}
                  note="Currently implementing"
                  tone="progress"
                />

                <StatusItem
                  label="Delayed"
                  value={delayedCount}
                  note="Timeline requires attention"
                  tone="delayed"
                />

              </div>

            </div>

          </div>

        </div>

        {/* SIGNAL FREQUENCY */}

        <div className="analytics-panel signal-frequency-panel">

          <div className="analytics-panel-header">

            <div>

              <span>
                ANOMALY SIGNAL FREQUENCY
              </span>

              <h3>
                What is driving project alerts?
              </h3>

            </div>

            <div className="signal-note">
              Multiple signals can occur
              in the same project.
            </div>

          </div>

          <div className="signal-frequency-grid">

            <SignalFrequency
              label="Unusual Spending"
              value={spendingSignals}
              total={projects.length}
              tone="blue"
              icon="₹"
            />

            <SignalFrequency
              label="Similar / Duplicate Work"
              value={duplicateSignals}
              total={projects.length}
              tone="purple"
              icon="▤"
            />

            <SignalFrequency
              label="Execution Delay"
              value={delaySignals}
              total={projects.length}
              tone="amber"
              icon="◷"
            />

            <SignalFrequency
              label="Cost Anomaly"
              value={costSignals}
              total={projects.length}
              tone="red"
              icon="!"
            />

            <SignalFrequency
              label="ML Anomaly"
              value={mlCount}
              total={projects.length}
              tone="green"
              icon="AI"
            />

          </div>

        </div>

      </section>

      {/* ======================================================
          RISK CATEGORIES
      ====================================================== */}

      <section className="portal-width section-block">

        <div className="center-title">

          <span>
            RISK SIGNAL CATEGORIES
          </span>

          <h2>
            What PRISM AI evaluates
          </h2>

          <div></div>

        </div>

        <div className="category-grid">

          <RiskCategoryCard
            icon="₹"
            title="Cost Anomalies"
            text="Identify unusual expenditure and deviations from sanctioned amounts."
            tone="red"
          />

          <RiskCategoryCard
            icon="◷"
            title="Project Delays"
            text="Compare planned and elapsed duration to detect abnormal execution delays."
            tone="red"
          />

          <RiskCategoryCard
            icon="▤"
            title="Similar Works"
            text="Use work-description similarity to surface potentially overlapping projects."
            tone="purple"
          />

          <RiskCategoryCard
            icon="▥"
            title="Spending Patterns"
            text="Compare project expenditure with category-level spending behaviour."
            tone="green"
          />

          <RiskCategoryCard
            icon="AI"
            title="ML Anomalies"
            text="Isolation Forest screens multiple numerical features for unusual patterns."
            tone="purple"
          />

          <RiskCategoryCard
            icon="◈"
            title="Explainable Risk"
            text="Combine evidence into a transparent project-level risk assessment."
            tone="blue"
          />

        </div>

      </section>

      {/* ======================================================
          PROCESS
      ====================================================== */}

      <section className="portal-width section-block">

        <div className="center-title">

          <span>
            HOW PRISM AI WORKS
          </span>

          <h2>
            From Data to Human Review
          </h2>

          <div></div>

        </div>

        <div className="process-grid">

          <ProcessStep
            number="01"
            title="MPLADS Data"
            text="Project details, expenditure, timeline, category and work descriptions."
            tone="blue"
          />

          <ProcessArrow />

          <ProcessStep
            number="02"
            title="AI Analysis"
            text="Cost, delay, similarity, spending and multivariate ML signals."
            tone="purple"
          />

          <ProcessArrow />

          <ProcessStep
            number="03"
            title="Risk Intelligence"
            text="Calculate transparent scores and explain why a project is prioritized."
            tone="red"
          />

          <ProcessArrow />

          <ProcessStep
            number="04"
            title="Human Review"
            text="Authorized officials validate context and decide appropriate action."
            tone="green"
          />

        </div>

      </section>

      {/* ======================================================
          PRIORITY PROJECTS
      ====================================================== */}

      <section
        id="priority-section"
        className="portal-width section-block"
      >

        <div className="section-title-row">

          <div>

            <span>
              PROJECT MONITORING
            </span>

            <h2>
              Priority Projects
            </h2>

          </div>

          <div className="result-count">

            Showing{" "}

            <strong>
              {filteredProjects.length}
            </strong>{" "}

            records

          </div>

        </div>

        <div className="project-toolbar">

          <div className="toolbar-search">

            <span>
              ⌕
            </span>

            <input
              value={search}
              onChange={(e) =>
                setSearch(
                  e.target.value
                )
              }
              placeholder="Search projects..."
            />

          </div>

          <div className="toolbar-filters">

            <select
              value={riskFilter}
              onChange={(e) =>
                setRiskFilter(
                  e.target.value
                )
              }
            >

              <option value="All">
                All Risk
              </option>

              <option value="High">
                High
              </option>

              <option value="Medium">
                Medium
              </option>

              <option value="Low">
                Low
              </option>

            </select>

            <select
              value={stateFilter}
              onChange={(e) =>
                setStateFilter(
                  e.target.value
                )
              }
            >

              <option>
                All States
              </option>

              {states.map(
                (item) => (
                  <option
                    key={item}
                    value={item}
                  >
                    {item}
                  </option>
                )
              )}

            </select>

            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(
                  e.target.value
                )
              }
            >

              <option>
                All Status
              </option>

              {statuses.map(
                (item) => (
                  <option
                    key={item}
                    value={item}
                  >
                    {item}
                  </option>
                )
              )}

            </select>

          </div>

        </div>

        {loading ? (
          <div className="portal-loading">

            <div className="loader"></div>

            Loading project records...

          </div>
        ) : (
          <div className="priority-list">

            {filteredProjects
              .slice(0, 20)
              .map((project, index) => (

                <div
                  className="priority-row animated-project-row"
                  style={{
                    "--row-delay": `${Math.min(
                      index * 60,
                      700
                    )}ms`,
                  }}
                  key={projectId(
                    project
                  )}
                  onClick={() =>
                    openProject(
                      projectId(
                        project
                      )
                    )
                  }
                >

                  <div className="priority-id">

                    <strong>
                      {projectId(
                        project
                      )}
                    </strong>

                    <span>
                      {category(
                        project
                      )}
                    </span>

                  </div>

                  <div className="priority-description">

                    <strong>
                      {description(
                        project
                      )}
                    </strong>

                    <span>
                      {district(
                        project
                      )},{" "}
                      {state(
                        project
                      )}
                    </span>

                  </div>

                  <div>

                    <span
                      className={`priority-risk ${
                        riskLevel(
                          project
                        ).toLowerCase()
                      }`}
                    >
                      {riskLevel(
                        project
                      )}
                    </span>

                  </div>

                  <div className="priority-score">

                    <strong>
                      {formatNumber(
                        riskScore(
                          project
                        )
                      )}
                    </strong>

                    <small>
                      / 100
                    </small>

                  </div>

                  <div>

                    {mlFlagged(
                      project
                    ) ? (
                      <span className="priority-ml">
                        ML FLAG
                      </span>
                    ) : (
                      <span className="priority-no-ml">
                        —
                      </span>
                    )}

                  </div>

                  <button
                    className="priority-open"
                    onClick={(e) => {
                      e.stopPropagation();

                      openProject(
                        projectId(
                          project
                        )
                      );
                    }}
                  >
                    Review →
                  </button>

                </div>

              ))}

            {filteredProjects.length ===
              0 && (
              <div className="portal-empty">
                No projects match the
                current filters.
              </div>
            )}

          </div>
        )}

      </section>

      {/* ======================================================
          INVESTIGATION
      ====================================================== */}

      {selectedProject && (
        <section
          ref={investigationRef}
          className="investigation-area"
        >

          <div className="portal-width">

            <div className="investigation-heading">

              <div>

                <span>
                  PROJECT INVESTIGATION
                </span>

                <h2>
                  {projectId(
                    selectedProject
                  )}
                </h2>

                <p>
                  {description(
                    selectedProject
                  )}
                </p>

              </div>

              <button
                className="close-button"
                onClick={() =>
                  setSelectedProject(
                    null
                  )
                }
              >
                ×
              </button>

            </div>

            {projectLoading ? (
              <div className="portal-loading">

                <div className="loader"></div>

                Loading investigation...

              </div>
            ) : (
              <>

                {/* RISK SUMMARY */}

                <div className="investigation-top-grid">

                  <div className="risk-summary-box">

                    <div
                      className="large-risk-circle"
                      style={{
                        "--progress": `${clamp(
                          riskScore(
                            selectedProject
                          )
                        )}%`,
                      }}
                    >

                      <div>

                        <span>
                          RISK
                        </span>

                        <strong>
                          {formatNumber(
                            riskScore(
                              selectedProject
                            )
                          )}
                        </strong>

                        <small>
                          / 100
                        </small>

                      </div>

                    </div>

                    <div>

                      <span className="box-label">
                        RULE-BASED RISK
                      </span>

                      <h3>
                        {riskLevel(
                          selectedProject
                        )}{" "}
                        Priority
                      </h3>

                      <p>
                        Transparent score using
                        cost, delay, similarity
                        and spending signals.
                      </p>

                    </div>

                  </div>

                  <div className="ml-summary-box">

                    <div className="ml-box-header">

                      <div>

                        <span>
                          AI / ML SIGNAL
                        </span>

                        <h3>
                          Isolation Forest
                        </h3>

                      </div>

                      <strong>
                        {mlFlagged(
                          selectedProject
                        )
                          ? "ANOMALY"
                          : "NORMAL"}
                      </strong>

                    </div>

                    <div className="ml-number">

                      {formatNumber(
                        mlScore(
                          selectedProject
                        )
                      )}

                      <small>
                        / 100
                      </small>

                    </div>

                    <div className="ml-progress">

                      <i
                        style={{
                          width: `${clamp(
                            mlScore(
                              selectedProject
                            )
                          )}%`,
                        }}
                      ></i>

                    </div>

                    <p>
                      Independent anomaly
                      screening across multiple
                      numerical project features.
                    </p>

                  </div>

                </div>

                {/* SIGNAL STRIP */}

                <div className="investigation-signal-grid">

                  <InvestigationSignal
                    title="Cost Overrun"
                    value={formatPercent(
                      selectedProject.sanction_overrun_pct
                    )}
                    note="vs sanctioned amount"
                    tone="red"
                  />

                  <InvestigationSignal
                    title="Execution Delay"
                    value={formatPercent(
                      selectedProject.delay_pct
                    )}
                    note={`${selectedProject.delay_days ?? "—"} days`}
                    tone="amber"
                  />

                  <InvestigationSignal
                    title="Work Similarity"
                    value={formatPercent(
                      selectedProject.max_similarity_pct
                    )}
                    note={`${selectedProject.similar_project_count ?? 0} related records`}
                    tone="purple"
                  />

                  <InvestigationSignal
                    title="Spending Z-Score"
                    value={formatNumber(
                      selectedProject.spending_zscore
                    )}
                    note="category benchmark"
                    tone="blue"
                  />

                </div>

                {/* MODEL NOTE */}

                <div className="model-note">

                  <div className="model-check">
                    ✓
                  </div>

                  <div>

                    <strong>
                      {mlFlagged(
                        selectedProject
                      )
                        ? "Both rule-based and ML systems flag this project for review."
                        : "Rule-based risk remains the primary review signal for this project."}
                    </strong>

                    <p>
                      Isolation Forest provides
                      an anomaly signal, not proof
                      of fraud. Final assessment
                      remains with authorized
                      officials.
                    </p>

                  </div>

                </div>

                {/* INVESTIGATION COLUMNS */}

                <div className="investigation-columns">

                  <div className="investigation-white">

                    <SectionMiniTitle
                      title="Risk Contribution"
                      subtitle="Explainable signals"
                    />

                    <RiskContribution
                      label="Cost Risk"
                      value={
                        selectedProject.cost_score
                      }
                      note="Financial deviation"
                      tone="red"
                    />

                    <RiskContribution
                      label="Delay Risk"
                      value={
                        selectedProject.delay_score
                      }
                      note="Timeline deviation"
                      tone="amber"
                    />

                    <RiskContribution
                      label="Duplicate Risk"
                      value={
                        selectedProject.duplicate_score
                      }
                      note="Text similarity"
                      tone="purple"
                    />

                    <RiskContribution
                      label="Spending Risk"
                      value={
                        selectedProject.spending_score
                      }
                      note="Spending pattern"
                      tone="blue"
                    />

                    <RiskContribution
                      label="ML Anomaly"
                      value={mlScore(
                        selectedProject
                      )}
                      note="Isolation Forest"
                      tone="green"
                    />

                  </div>

                  <div className="investigation-white">

                    <SectionMiniTitle
                      title="Project Snapshot"
                      subtitle="Financial & execution context"
                    />

                    <div className="snapshot-grid">

                      <Snapshot
                        label="Estimated Cost"
                        value={
                          selectedProject.estimated_cost_lakh !=
                          null
                            ? `₹${formatNumber(
                                selectedProject.estimated_cost_lakh
                              )} L`
                            : "—"
                        }
                      />

                      <Snapshot
                        label="Sanctioned"
                        value={
                          selectedProject.sanctioned_amount_lakh !=
                          null
                            ? `₹${formatNumber(
                                selectedProject.sanctioned_amount_lakh
                              )} L`
                            : "—"
                        }
                      />

                      <Snapshot
                        label="Expenditure"
                        value={
                          selectedProject.expenditure_lakh !=
                          null
                            ? `₹${formatNumber(
                                selectedProject.expenditure_lakh
                              )} L`
                            : "—"
                        }
                      />

                      <Snapshot
                        label="Physical Progress"
                        value={formatPercent(
                          selectedProject.physical_progress_pct
                        )}
                      />

                      <Snapshot
                        label="Planned Duration"
                        value={
                          selectedProject.planned_duration_days !=
                          null
                            ? `${selectedProject.planned_duration_days} days`
                            : "—"
                        }
                      />

                      <Snapshot
                        label="Elapsed"
                        value={
                          selectedProject.elapsed_days !=
                          null
                            ? `${selectedProject.elapsed_days} days`
                            : "—"
                        }
                      />

                      <Snapshot
                        label="Status"
                        value={
                          selectedProject.current_status ??
                          "—"
                        }
                      />

                      <Snapshot
                        label="Agency"
                        value={
                          selectedProject.implementing_agency ??
                          "—"
                        }
                      />

                    </div>

                  </div>

                </div>

                {/* EXPLAINABLE REASONS */}

                <div className="investigation-white reasons-section">

                  <SectionMiniTitle
                    title="Explainable Alerts"
                    subtitle="Why this project was prioritized"
                  />

                  <div className="reason-grid">

                    {reasons(
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
                            ).padStart(
                              2,
                              "0"
                            )}
                          </span>

                          <div>

                            <strong>
                              Review signal
                            </strong>

                            <p>
                              {reason}
                            </p>

                          </div>

                        </div>
                      )
                    )}

                    {mlFlagged(
                      selectedProject
                    ) && (
                      <div className="reason-item ml-reason">

                        <span>
                          ML
                        </span>

                        <div>

                          <strong>
                            Isolation Forest anomaly
                          </strong>

                          <p>
                            An unusual
                            multivariate pattern
                            was detected across
                            project features.
                          </p>

                        </div>

                      </div>
                    )}

                  </div>

                </div>

                {/* COMPARABLE PROJECTS */}

                <div className="investigation-white">

                  <SectionMiniTitle
                    title="Comparable Projects"
                    subtitle="Context from similar records"
                  />

                  {comparablesLoading ? (
                    <div className="portal-loading compact">

                      <div className="loader"></div>

                      Loading comparable projects...

                    </div>
                  ) : comparables.length ===
                    0 ? (
                    <div className="portal-empty compact">
                      No comparable projects
                      available.
                    </div>
                  ) : (
                    <div className="comparables">

                      <div className="comparison-head">

                        <span>
                          Project
                        </span>

                        <span>
                          Category
                        </span>

                        <span>
                          Expenditure
                        </span>

                        <span>
                          Risk
                        </span>

                        <span>
                          Similarity
                        </span>

                      </div>

                      {comparables
                        .slice(0, 5)
                        .map(
                          (item) => (
                            <div
                              className="comparison-row"
                              key={projectId(
                                item
                              )}
                            >

                              <strong>
                                {projectId(
                                  item
                                )}
                              </strong>

                              <span>
                                {category(
                                  item
                                )}
                              </span>

                              <span>
                                {item.expenditure_lakh !=
                                null
                                  ? `₹${formatNumber(
                                      item.expenditure_lakh
                                    )} L`
                                  : "—"}
                              </span>

                              <span
                                className={
                                  `comparison-risk ${
                                    riskLevel(
                                      item
                                    ).toLowerCase()
                                  }`
                                }
                              >
                                {formatNumber(
                                  riskScore(
                                    item
                                  )
                                )}
                              </span>

                              <span>
                                {item.similarity_pct !=
                                null
                                  ? formatPercent(
                                      item.similarity_pct
                                    )
                                  : "—"}
                              </span>

                            </div>
                          )
                        )}

                    </div>
                  )}

                </div>

                {/* HUMAN REVIEW */}

                <div className="human-review">

                  <div className="review-check">
                    ✓
                  </div>

                  <div>

                    <span>
                      RECOMMENDED ACTION
                    </span>

                    <h3>
                      Human Review Required
                    </h3>

                    <p>
                      PRISM AI prioritizes
                      potential anomalies and
                      explains the underlying
                      signals. Authorized
                      officials make the final
                      verification and decision.
                    </p>

                  </div>

                </div>

              </>
            )}

          </div>

        </section>
      )}

      {/* ======================================================
          ANALYSIS ANIMATION
      ====================================================== */}

      {analysisRunning &&
        selectedProject && (
          <div className="prism-analysis-overlay">

            <div className="analysis-box">

              <div className="analysis-logo">
                PRISM AI
              </div>

              <div className="analysis-title">
                ANALYZING PROJECT
              </div>

              <div className="analysis-project-id">
                {projectId(
                  selectedProject
                )}
              </div>

              <div className="analysis-progress">

                <AnalysisStep
                  number="01"
                  text="Financial signals analyzed"
                  active={analysisStep >= 1}
                />

                <AnalysisStep
                  number="02"
                  text="Timeline signals analyzed"
                  active={analysisStep >= 2}
                />

                <AnalysisStep
                  number="03"
                  text="Work-description similarity analyzed"
                  active={analysisStep >= 3}
                />

                <AnalysisStep
                  number="04"
                  text="Spending pattern analyzed"
                  active={analysisStep >= 4}
                />

                <AnalysisStep
                  number="05"
                  text="Isolation Forest screening complete"
                  active={analysisStep >= 5}
                />

              </div>

              <div className="analysis-line">

                <i
                  style={{
                    width: `${analysisStep * 20}%`,
                  }}
                ></i>

              </div>

              <div className="analysis-status">
                {analysisStep < 5
                  ? "PRISM AI is analyzing project signals..."
                  : "Risk intelligence generated"}
              </div>

            </div>

          </div>
        )}

      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer className="portal-footer">

        <div className="portal-width footer-inner">

          <div>

            <strong>
              PRISM AI
            </strong>

            <span>
              MPLADS Risk Intelligence System
            </span>

          </div>

          <div>
            AI-assisted monitoring ·
            Human decision remains final
          </div>

        </div>

      </footer>

    </div>
  );
}

// ============================================================
// COMPONENTS
// ============================================================

function PortalStat({
  icon,
  value,
  label,
  tone = "blue",
}) {
  return (
    <div
      className={`portal-stat animate-stat ${tone}`}
    >

      <div
        className={`portal-stat-icon ${tone}`}
      >
        {icon}
      </div>

      <div>

        <AnimatedNumber
          value={value}
        />

        <span>
          {label}
        </span>

      </div>

    </div>
  );
}

function AnimatedNumber({
  value,
}) {
  const numericValue =
    Number(value);

  const [display, setDisplay] =
    useState(
      Number.isFinite(numericValue)
        ? 0
        : value
    );

  useEffect(() => {
    if (
      !Number.isFinite(
        numericValue
      )
    ) {
      setDisplay(value);
      return;
    }

    const duration = 900;
    const startTime =
      performance.now();

    const animate = (time) => {
      const progress = Math.min(
        (time - startTime) /
          duration,
        1
      );

      const eased =
        1 -
        Math.pow(
          1 - progress,
          3
        );

      setDisplay(
        Math.round(
          numericValue *
            eased
        )
      );

      if (progress < 1) {
        requestAnimationFrame(
          animate
        );
      }
    };

    requestAnimationFrame(
      animate
    );
  }, [numericValue, value]);

  return (
    <strong>
      {Number.isFinite(numericValue)
        ? display
        : value}
    </strong>
  );
}

function RiskCategoryCard({
  icon,
  title,
  text,
  tone,
}) {
  return (
    <div className="category-card">

      <div
        className={`category-icon ${tone}`}
      >
        {icon}
      </div>

      <div>

        <h3>
          {title}
        </h3>

        <p>
          {text}
        </p>

      </div>

    </div>
  );
}

function ProcessStep({
  number,
  title,
  text,
  tone,
}) {
  return (
    <div className="process-step">

      <span
        className={`process-number ${tone}`}
      >
        {number}
      </span>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

    </div>
  );
}

function ProcessArrow() {
  return (
    <div className="process-arrow">
      →
    </div>
  );
}

function ChartBar({
  label,
  value,
  total,
  tone,
}) {
  const percentage = total
    ? (value / total) * 100
    : 0;

  return (
    <div className="chart-bar-row">

      <div className="chart-bar-label">
        {label}
      </div>

      <div className="chart-bar-track">

        <i
          className={tone}
          style={{
            width: `${percentage}%`,
          }}
        ></i>

      </div>

      <span>
        {percentage.toFixed(1)}%
      </span>

    </div>
  );
}

function StatusItem({
  label,
  value,
  note,
  tone,
}) {
  return (
    <div className="status-item">

      <span
        className={`status-marker ${tone}`}
      ></span>

      <div>

        <strong>
          {label}
        </strong>

        <small>
          {note}
        </small>

      </div>

      <b>
        {value}
      </b>

    </div>
  );
}

function SignalFrequency({
  label,
  value,
  total,
  tone,
  icon,
}) {
  const percentage = total
    ? (value / total) * 100
    : 0;

  return (
    <div className="signal-frequency-card">

      <div className="signal-frequency-top">

        <div
          className={`frequency-icon ${tone}`}
        >
          {icon}
        </div>

        <div>

          <strong>
            {label}
          </strong>

          <small>
            {value} projects
          </small>

        </div>

      </div>

      <div className="frequency-bar">

        <i
          className={tone}
          style={{
            width: `${Math.min(
              100,
              percentage
            )}%`,
          }}
        ></i>

      </div>

      <div className="frequency-bottom">

        <span>
          Signal frequency
        </span>

        <b>
          {percentage.toFixed(1)}%
        </b>

      </div>

    </div>
  );
}

function InvestigationSignal({
  title,
  value,
  note,
  tone,
}) {
  return (
    <div
      className={`investigation-signal ${tone}`}
    >

      <span>
        {title}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {note}
      </small>

    </div>
  );
}

function RiskContribution({
  label,
  value,
  tone,
  note,
}) {
  const number =
    Number(value) || 0;

  return (
    <div className="risk-contribution">

      <div className="risk-contribution-top">

        <div>

          <span
            className={`contribution-dot ${tone}`}
          ></span>

          <strong>
            {label}
          </strong>

        </div>

        <b>
          {number.toFixed(2)}
        </b>

      </div>

      <div className="contribution-track">

        <i
          className={tone}
          style={{
            width: `${Math.max(
              0,
              Math.min(
                100,
                number
              )
            )}%`,
          }}
        ></i>

      </div>

      <small>
        {note}
      </small>

    </div>
  );
}

function Snapshot({
  label,
  value,
}) {
  return (
    <div className="snapshot-item">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}

function SectionMiniTitle({
  title,
  subtitle,
}) {
  return (
    <div className="section-mini-title">

      <span>
        {subtitle}
      </span>

      <h3>
        {title}
      </h3>

    </div>
  );
}

function AnalysisStep({
  number,
  text,
  active,
}) {
  return (
    <div
      className={`analysis-step ${
        active ? "active" : ""
      }`}
    >

      <span>
        {active ? "✓" : number}
      </span>

      <strong>
        {text}
      </strong>

    </div>
  );
}

export default App;