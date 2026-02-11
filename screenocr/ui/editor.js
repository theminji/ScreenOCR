const editor = document.getElementById("editor");
const lineNumbers = document.getElementById("lineNumbers");
const wordCount = document.getElementById("wordCount");
const copyBtn = document.getElementById("copyBtn");
const saveBtn = document.getElementById("saveBtn");
const closeBtn = document.getElementById("closeBtn");

function updateLineNumbers() {
  const lineCount = editor.value.split("\n").length;
  let output = "";
  for (let i = 1; i <= lineCount; i += 1) {
    output += `${i}\n`;
  }
  lineNumbers.textContent = output;
}

function updateWordCount() {
  const words = editor.value.trim() ? editor.value.trim().split(/\s+/).length : 0;
  wordCount.textContent = `WORDS: ${words}`;
}

function refreshMeta() {
  updateLineNumbers();
  updateWordCount();
}

editor.addEventListener("input", refreshMeta);
editor.addEventListener("scroll", () => {
  lineNumbers.scrollTop = editor.scrollTop;
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(editor.value);
  } catch (_err) {
    editor.focus();
    editor.select();
    document.execCommand("copy");
  }
});

saveBtn.addEventListener("click", async () => {
  await window.pywebview.api.save_text(editor.value);
});

closeBtn.addEventListener("click", async () => {
  await window.pywebview.api.close_window();
});

window.addEventListener("pywebviewready", async () => {
  const initialText = await window.pywebview.api.get_initial_text();
  editor.value = initialText || "";
  refreshMeta();
});

