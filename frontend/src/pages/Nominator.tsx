import { useEffect, useState } from "react";
import { getHealth, rankFaculty, type Health, type RankingRow } from "../api/client";

export function Nominator() {
  const [health, setHealth] = useState<Health | null>(null);
  const [criteria, setCriteria] = useState("");
  const [department, setDepartment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [raw, setRaw] = useState<string | null>(null);
  const [rows, setRows] = useState<RankingRow[] | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function run() {
    setError(null);
    setRaw(null);
    setRows(null);
    setLoading(true);
    try {
      const res = await rankFaculty(criteria, department || undefined);
      setRaw(res.raw_response);
      setRows(res.rankings);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page single">
      <section className="panel card-elevated">
        <h2 className="panel-title">Committee matching</h2>
        <p className="panel-intro">
          Describe the award or paste official criteria. The backend embeds your
          text, pulls the closest CV chunks from Pinecone, and asks the TAMU AI
          model for a top-ten style ranking with reasoning.
        </p>
        {health && (
          <p
            className={
              health.config_ok ? "status-pill ok" : "status-pill warn"
            }
          >
            {health.config_ok
              ? "Pinecone + TAMU API configured"
              : (health.config_error ?? "Configure API keys")}
          </p>
        )}

        <label className="label" htmlFor="criteria">
          Award criteria
        </label>
        <textarea
          id="criteria"
          className="textarea"
          rows={12}
          value={criteria}
          onChange={(e) => setCriteria(e.target.value)}
          placeholder="Paste or write the full award criteria, eligibility, and emphasis areas…"
        />

        <label className="label" htmlFor="dept">
          Optional name filter
        </label>
        <input
          id="dept"
          className="input"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          placeholder="Substring of faculty / CV filename stem (e.g. department keyword)"
        />
        <p className="hint">
          CVs are keyed by PDF filename in Pinecone metadata; use a substring that
          appears in those names to narrow the pool before the LLM step.
        </p>

        <button
          type="button"
          className="btn primary"
          disabled={loading || criteria.trim().length < 20}
          onClick={() => void run()}
        >
          {loading ? "Retrieving & ranking…" : "Generate top matches"}
        </button>
        {error && <p className="error">{error}</p>}

        {rows && rows.length > 0 && (
          <div className="rank-block">
            <h3 className="subhead">Ranked short list</h3>
            <ol className="rank-list">
              {rows.map((r) => (
                <li key={`${r.rank}-${r.faculty_name}`}>
                  <div className="rank-head">
                    <span className="rank-num">#{r.rank}</span>
                    <span className="rank-name">{r.faculty_name}</span>
                    <span className="rank-score">Score {r.match_score}/10</span>
                  </div>
                  <p className="rank-reason">{r.reasoning}</p>
                </li>
              ))}
            </ol>
          </div>
        )}

        {raw && (!rows || rows.length === 0) && (
          <div className="rank-block">
            <h3 className="subhead">Model output</h3>
            <p className="hint">
              JSON parsing failed or the model used a different format. Raw
              response is shown below.
            </p>
            <pre className="detail-block">{raw}</pre>
          </div>
        )}
      </section>
    </div>
  );
}
