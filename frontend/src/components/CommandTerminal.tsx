import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { FastForward, Loader2, Terminal as TerminalIcon } from "lucide-react";
import CommandItem from "./CommandItem";

interface Step {
  command: string;
  explanation: string;
}

interface CommandTerminalProps {
  steps: Step[];
  isLoading: boolean;
  onPromptClick?: (prompt: string) => void;
}

const CommandTerminal = ({ steps, isLoading, onPromptClick }: CommandTerminalProps) => {
  const [displayedSteps, setDisplayedSteps] = useState<Step[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [skipAnimation, setSkipAnimation] = useState(false);

  useEffect(() => {
    if (steps.length === 0) {
      setDisplayedSteps([]);
      setCurrentIndex(0);
      setIsTyping(false);
      setSkipAnimation(false);
      return;
    }

    if (skipAnimation) {
      setDisplayedSteps(steps);
      setIsTyping(false);
      return;
    }

    setIsTyping(true);
    setDisplayedSteps([]);
    setCurrentIndex(0);
  }, [steps, skipAnimation]);

  useEffect(() => {
    if (skipAnimation || !isTyping || currentIndex >= steps.length) {
      if (currentIndex >= steps.length && steps.length > 0) {
        setIsTyping(false);
      }
      return;
    }

    const timer = setTimeout(() => {
      setDisplayedSteps(prev => [...prev, steps[currentIndex]]);
      setCurrentIndex(prev => prev + 1);
    }, 400);

    return () => clearTimeout(timer);
  }, [currentIndex, steps, isTyping, skipAnimation]);

  const handleSkip = () => {
    setSkipAnimation(true);
    setDisplayedSteps(steps);
    setIsTyping(false);
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 pb-6">
        <div className="terminal-container scanlines p-8">
          <div className="flex flex-col items-center justify-center gap-4 py-12">
            <Loader2 className="h-8 w-8 terminal-text animate-spin terminal-glow" />
            <p className="terminal-muted text-sm animate-pulse">Processing your prompt...</p>
          </div>
        </div>
      </div>
    );
  }

  if (steps.length === 0) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 pb-6">
        <div className="terminal-container scanlines p-8">
          <div className="flex flex-col items-center justify-center gap-6 py-12">
            <TerminalIcon className="h-16 w-16 terminal-muted" />
            <div className="text-center space-y-3">
              <p className="terminal-text text-lg">Ready to generate shell commands</p>
              <p className="terminal-muted text-sm">Enter a prompt above to get started</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center mt-4">
              {[
                "List all files modified today",
                "Find large files over 100MB",
                "Check disk usage by directory",
              ].map((example, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => onPromptClick?.(example)}
                  className="px-3 py-1.5 text-xs terminal-muted border border-border/40 rounded hover:border-primary/50 hover:terminal-text transition-colors cursor-pointer"
                >
                  {example}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6">
      <div className="terminal-container scanlines p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-border/40 pb-3">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-error/60" />
              <div className="w-3 h-3 rounded-full bg-warning/60" />
              <div className="w-3 h-3 rounded-full bg-success/60" />
            </div>
            <span className="text-xs terminal-muted ml-2">terminal</span>
          </div>
          
          {isTyping && !skipAnimation && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="text-xs terminal-muted hover:terminal-text"
            >
              <FastForward className="h-3 w-3 mr-1" />
              Skip animation
            </Button>
          )}
        </div>

        <div className="space-y-4 font-mono text-sm">
          {displayedSteps.map((step, index) => (
            <div key={index}>
              <CommandItem
                command={step.command}
                explanation={step.explanation}
                index={index}
              />
            </div>
          ))}
          
          {isTyping && !skipAnimation && (
            <div className="flex items-center gap-2">
              <span className="terminal-accent font-bold">$</span>
              <div className="typing-cursor" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CommandTerminal;
