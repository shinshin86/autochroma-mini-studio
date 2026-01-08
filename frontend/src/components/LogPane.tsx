interface LogPaneProps {
  lines: string[];
}

export function LogPane({ lines }: LogPaneProps) {
  if (lines.length === 0) return null;

  return (
    <div className="log-pane">
      <h3>ログ</h3>
      <pre className="log-output">
        {lines.join("\n")}
      </pre>
    </div>
  );
}
