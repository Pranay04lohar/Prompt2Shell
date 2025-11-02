import { useState } from "react";
import { Copy, Play, Info, Check, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";

interface CommandItemProps {
  command: string;
  explanation: string;
  index: number;
}

const CommandItem = ({ command, explanation, index }: CommandItemProps) => {
  const [copied, setCopied] = useState(false);
  const [showOutput, setShowOutput] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error("Failed to copy");
    }
  };

  const handleRun = () => {
    setShowOutput(!showOutput);
  };

  // Simple risk assessment based on command content
  const getRiskLevel = (cmd: string): "low" | "medium" | "high" => {
    const highRiskKeywords = ["rm", "delete", "drop", "truncate", "shutdown"];
    const mediumRiskKeywords = ["mv", "chmod", "chown", "kill"];
    
    if (highRiskKeywords.some(keyword => cmd.toLowerCase().includes(keyword))) {
      return "high";
    }
    if (mediumRiskKeywords.some(keyword => cmd.toLowerCase().includes(keyword))) {
      return "medium";
    }
    return "low";
  };

  const riskLevel = getRiskLevel(command);
  const riskColors = {
    low: "terminal-accent",
    medium: "text-warning",
    high: "text-error",
  };

  // Mock output based on command
  const generateMockOutput = () => {
    const outputs = [
      "Found 12 files\n./src/components/CommandItem.tsx\n./src/components/Header.tsx\n./src/App.tsx\n...",
      "Command executed successfully\nProcessing...\nDone.",
      "Output:\ntotal 48\n-rw-r--r-- 1 user user 1234 Jan 1 12:00 file.txt\n...",
    ];
    return outputs[index % outputs.length];
  };

  return (
    <div className="space-y-2 animate-[fadeIn_0.3s_ease-out]">
      <div className="flex items-start gap-3 group">
        <span className="terminal-accent font-bold mt-1">$</span>
        <div className="flex-1 min-w-0">
          <code className="text-sm terminal-text break-all">{command}</code>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 hover:bg-muted/30"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <Check className="h-4 w-4 terminal-accent" />
                  ) : (
                    <Copy className="h-4 w-4 terminal-muted" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent className="bg-popover border-border/60">
                <p className="text-xs">Copy command</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 hover:bg-muted/30"
                  onClick={handleRun}
                >
                  {showOutput ? (
                    <ChevronDown className="h-4 w-4 terminal-accent" />
                  ) : (
                    <Play className="h-4 w-4 terminal-muted" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent className="bg-popover border-border/60">
                <p className="text-xs">Simulate run</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 hover:bg-muted/30"
                >
                  <Info className="h-4 w-4 terminal-muted" />
                </Button>
              </TooltipTrigger>
              <TooltipContent className="bg-popover border-border/60 max-w-sm">
                <p className="text-xs terminal-text mb-2">{explanation}</p>
                <p className={`text-xs ${riskColors[riskLevel]} font-semibold`}>
                  Risk: {riskLevel.toUpperCase()}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {showOutput && (
        <div className="ml-6 pl-4 border-l-2 border-border/40 animate-[fadeIn_0.2s_ease-out]">
          <div className="bg-input/30 rounded p-3 text-xs terminal-muted space-y-1">
            <div className="flex items-center gap-2 mb-2">
              <ChevronRight className="h-3 w-3 terminal-accent" />
              <span className="terminal-accent">Simulated output:</span>
            </div>
            <pre className="whitespace-pre-wrap">{generateMockOutput()}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommandItem;
