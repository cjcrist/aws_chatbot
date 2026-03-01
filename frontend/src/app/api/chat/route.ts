import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl = process.env.CHAT_API_URL || "http://chatbot:8000";

type IncomingPayload = {
  query?: string;
  user_id?: string;
};

export async function POST(request: NextRequest) {
  let payload: IncomingPayload;
  try {
    payload = (await request.json()) as IncomingPayload;
  } catch {
    return NextResponse.json({ error: "Invalid JSON payload" }, { status: 400 });
  }

  const query = payload.query?.trim();
  const user_id = payload.user_id?.trim();

  if (!query) {
    return NextResponse.json({ error: "query is required" }, { status: 400 });
  }

  try {
    const backendResponse = await fetch(`${backendBaseUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ query, user_id })
    });

    if (!backendResponse.ok) {
      const backendText = await backendResponse.text();
      return NextResponse.json(
        {
          error: `Backend error (${backendResponse.status}): ${backendText || "unknown"}`
        },
        { status: backendResponse.status }
      );
    }

    const data = (await backendResponse.json()) as { answer?: string };
    return NextResponse.json({ answer: data.answer ?? "" }, { status: 200 });
  } catch (error) {
    const details = error instanceof Error ? error.message : "Unknown proxy error";
    return NextResponse.json({ error: `Unable to reach backend: ${details}` }, { status: 502 });
  }
}
