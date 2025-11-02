import { useState, useEffect } from "react";
import { toast } from "sonner";
import Header from "@/components/Header";
import PromptInput from "@/components/PromptInput";
import CommandTerminal from "@/components/CommandTerminal";
import Footer from "@/components/Footer";
import { generateCommands, saveToHistory, checkHealth, APIError } from "@/lib/api";

interface Step {
  command: string;
  explanation: string;
}

const Index = () => {
  const [steps, setSteps] = useState<Step[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [modelName, setModelName] = useState(" Phi-3-mini (QLoRA Fine-Tuned)");
  const [apiStatus, setApiStatus] = useState<"connected" | "disconnected" | "loading">("loading");
  const [inputPrompt, setInputPrompt] = useState("");

  // Check API health on mount
  useEffect(() => {
    const checkApiHealth = async () => {
      const isHealthy = await checkHealth();
      setApiStatus(isHealthy ? "connected" : "disconnected");
    };
    
    checkApiHealth();
  }, []);

  const handleSubmit = async (prompt: string) => {
    setIsLoading(true);
    setSteps([]);
    setInputPrompt(prompt); // Update input field with the prompt
    
    try {
      const response = await generateCommands(prompt);
      setSteps(response.steps);
      setModelName(response.model);
      saveToHistory(prompt);
      
      if (apiStatus !== "connected") {
        setApiStatus("connected");
      }
    } catch (error) {
      console.error("Failed to generate commands:", error);
      
      if (error instanceof APIError) {
        if (error.status === 404) {
          toast.error("API endpoint not found. Please check your backend configuration.");
        } else if (error.status === 500) {
          toast.error("Server error. Please try again later.");
        } else {
          toast.error(error.message || "Failed to generate commands");
        }
        setApiStatus("disconnected");
      } else {
        toast.error("Failed to connect to the API. Please check your connection.");
        setApiStatus("disconnected");
      }
      
      // Show example data in case of error (for demonstration)
      setSteps([
        {
          command: "find . -type f -mtime -1",
          explanation: "Find all files modified in the last 24 hours"
        },
        {
          command: "ls -lht | head -20",
          explanation: "List the 20 most recently modified files with details"
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background scanlines">
      <Header modelName={modelName} apiStatus={apiStatus} />
      
      <div className="flex-1 py-6">
        <PromptInput onSubmit={handleSubmit} isLoading={isLoading} initialValue={inputPrompt} />
        <CommandTerminal steps={steps} isLoading={isLoading} onPromptClick={handleSubmit} />
      </div>

      <Footer />
    </div>
  );
};

export default Index;
