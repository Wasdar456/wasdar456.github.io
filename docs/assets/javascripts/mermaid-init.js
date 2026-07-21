mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict"
});

function renderMermaidDiagrams() {
  return mermaid.run({ querySelector: ".mermaid" });
}

// Render the initial document and every page reached through instant navigation.
renderMermaidDiagrams();
document$.subscribe(renderMermaidDiagrams);
