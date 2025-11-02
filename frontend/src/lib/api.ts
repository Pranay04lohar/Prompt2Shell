// API configuration and utilities for Prompt2Shell

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export interface GenerateRequest {
  prompt: string;
}

export interface GenerateResponse {
  model: string;
  steps: {
    command: string;
    explanation: string;
  }[];
}

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * Generate shell commands from a natural language prompt
 */
export async function generateCommands(prompt: string): Promise<GenerateResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.message || `API request failed with status ${response.status}`,
        response.status,
        errorData
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    // Network or other errors
    throw new APIError(
      error instanceof Error ? error.message : "Failed to connect to API",
      undefined,
      error
    );
  }
}

/**
 * Check API health status (optional endpoint)
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
    });
    return response.ok;
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
}

/**
 * Save prompt to localStorage history
 */
export function saveToHistory(prompt: string) {
  try {
    const history = getHistory();
    const newHistory = [prompt, ...history.filter(p => p !== prompt)].slice(0, 50); // Keep last 50
    localStorage.setItem("prompt-history", JSON.stringify(newHistory));
  } catch (error) {
    console.error("Failed to save to history:", error);
  }
}

/**
 * Get prompt history from localStorage
 */
export function getHistory(): string[] {
  try {
    const stored = localStorage.getItem("prompt-history");
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error("Failed to get history:", error);
    return [];
  }
}
