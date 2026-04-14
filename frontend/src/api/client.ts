const base = "";

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        if (d && typeof d === "object" && "msg" in d)
          return String((d as { msg: unknown }).msg);
        return JSON.stringify(d);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Request failed";
}

async function readErrorMessage(r: Response): Promise<string> {
  try {
    const err = await r.json();
    if (err && typeof err === "object" && "detail" in err)
      return formatDetail((err as { detail: unknown }).detail);
  } catch {
    /* ignore */
  }
  return r.statusText;
}

export type AwardSummary = {
  filename: string;
  title: string;
  preview: string;
};

export type Health = {
  status: string;
  config_ok: boolean;
  config_error: string | null;
  awards_extracted_count: number;
  pinecone_note: string;
};

export async function getHealth(): Promise<Health> {
  const r = await fetch(`${base}/api/health`);
  if (!r.ok) throw new Error("Health check failed");
  return r.json() as Promise<Health>;
}

export async function listAwards(q?: string): Promise<AwardSummary[]> {
  const url = q
    ? `${base}/api/awards?${new URLSearchParams({ q })}`
    : `${base}/api/awards`;
  const r = await fetch(url);
  if (!r.ok) throw new Error("Failed to load awards");
  const data = (await r.json()) as { awards: AwardSummary[] };
  return data.awards;
}

export async function getAward(filename: string): Promise<{ text: string }> {
  const r = await fetch(
    `${base}/api/awards/${encodeURIComponent(filename)}`,
  );
  if (!r.ok) throw new Error("Failed to load award");
  return r.json() as Promise<{ text: string }>;
}

export async function listCvs(): Promise<string[]> {
  const r = await fetch(`${base}/api/cvs`);
  if (!r.ok) throw new Error("Failed to load CVs");
  const data = (await r.json()) as { cvs: string[] };
  return data.cvs;
}

export async function getCvText(filename: string): Promise<{ text: string }> {
  const r = await fetch(`${base}/api/cvs/${encodeURIComponent(filename)}`);
  if (!r.ok) throw new Error("Failed to load CV");
  return r.json() as Promise<{ text: string }>;
}

export type ResumeMatch = {
  filename: string;
  score: number;
  preview: string;
  reasoning?: string;
  match_score?: number;
};

export async function matchResume(
  resumeText: string,
  topN = 10,
): Promise<ResumeMatch[]> {
  const r = await fetch(`${base}/api/nominee/match-resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, top_n: topN }),
  });
  if (!r.ok) throw new Error(await readErrorMessage(r));
  const data = (await r.json()) as { matches: ResumeMatch[] };
  return data.matches;
}

export type RankingRow = {
  rank: number;
  faculty_name: string;
  match_score: number;
  reasoning: string;
};

export async function rankFaculty(
  criteriaText: string,
  department?: string,
): Promise<{ raw_response: string; rankings: RankingRow[] | null }> {
  const r = await fetch(`${base}/api/nominator/rank-faculty`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      criteria_text: criteriaText,
      department: department?.trim() || null,
    }),
  });
  if (!r.ok) throw new Error(await readErrorMessage(r));
  return r.json() as Promise<{
    raw_response: string;
    rankings: RankingRow[] | null;
  }>;
}
