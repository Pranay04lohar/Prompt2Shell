import { useState, useEffect, KeyboardEvent } from "react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { CornerDownLeft, Delete } from "lucide-react";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
  initialValue?: string;
}

const PromptInput = ({ onSubmit, isLoading, initialValue }: PromptInputProps) => {
  const [prompt, setPrompt] = useState(initialValue || "");
  
  // Update prompt when initialValue changes
  useEffect(() => {
    if (initialValue !== undefined) {
      setPrompt(initialValue);
    }
  }, [initialValue]);

  const handleSubmit = () => {
    if (prompt.trim() && !isLoading) {
      onSubmit(prompt.trim());
      // Keep the prompt text after submission so users can see/edit it
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.ctrlKey && e.key === "k") {
      e.preventDefault();
      setPrompt("");
    }
  };

  const handleClear = () => {
    setPrompt("");
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="terminal-container p-6 space-y-4">
        <div className="flex items-center gap-2 terminal-accent">
          <span className="text-lg">{">"}</span>
          <span className="text-sm terminal-muted">Enter your command prompt</span>
        </div>
        
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="List all files modified in the last 24 hours"
          className="min-h-[100px] bg-input border-border/40 terminal-text resize-none focus:ring-2 focus:ring-primary/50 placeholder:terminal-muted"
          disabled={isLoading}
        />
        
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2 text-xs terminal-muted">
            <span className="flex items-center gap-1">
              <CornerDownLeft className="w-3 h-3" />
              <kbd className="px-1.5 py-0.5 rounded bg-muted/30 border border-border/40">Enter</kbd>
              <span>Generate</span>
            </span>
            <span className="flex items-center gap-1">
              <Delete className="w-3 h-3" />
              <kbd className="px-1.5 py-0.5 rounded bg-muted/30 border border-border/40">Ctrl+K</kbd>
              <span>Clear</span>
            </span>
          </div>
          
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
              disabled={!prompt || isLoading}
              className="flex-1 sm:flex-none border-border/40 hover:border-primary/50"
            >
              Clear
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim() || isLoading}
              className="flex-1 sm:flex-none bg-primary text-primary-foreground hover:bg-primary/90 terminal-glow"
            >
              {isLoading ? (
                <>
                  <span className="animate-pulse">&gt;_</span>
                  <span className="ml-2">Generating...</span>
                </>
              ) : (
                <>
                  <span>&gt;_</span>
                  <span className="ml-2">Generate</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptInput;
