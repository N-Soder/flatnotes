<template>
  <div class="flex flex-col h-full">
    <!-- Toolbar -->
    <div
      v-if="editor"
      class="flex flex-wrap gap-0.5 border-b border-theme-border pb-1 mb-2 print:hidden"
    >
      <ToolBtn
        :active="editor.isActive('bold')"
        title="Bold"
        @click="editor.chain().focus().toggleBold().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatBold" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('italic')"
        title="Italic"
        @click="editor.chain().focus().toggleItalic().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatItalic" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('strike')"
        title="Strikethrough"
        @click="editor.chain().focus().toggleStrike().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatStrikethrough" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('code')"
        title="Inline Code"
        @click="editor.chain().focus().toggleCode().run()"
      >
        <SvgIcon type="mdi" :path="mdiCodeTags" size="1.1em" />
      </ToolBtn>
      <div class="w-px bg-theme-border mx-0.5 self-stretch"></div>
      <ToolBtn
        :active="editor.isActive('heading', { level: 1 })"
        title="Heading 1"
        @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatHeader1" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('heading', { level: 2 })"
        title="Heading 2"
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatHeader2" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('heading', { level: 3 })"
        title="Heading 3"
        @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatHeader3" size="1.1em" />
      </ToolBtn>
      <div class="w-px bg-theme-border mx-0.5 self-stretch"></div>
      <ToolBtn
        :active="editor.isActive('bulletList')"
        title="Bullet List"
        @click="editor.chain().focus().toggleBulletList().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatListBulleted" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('orderedList')"
        title="Numbered List"
        @click="editor.chain().focus().toggleOrderedList().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatListNumbered" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('taskList')"
        title="Task List"
        @click="editor.chain().focus().toggleTaskList().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatListCheckbox" size="1.1em" />
      </ToolBtn>
      <div class="w-px bg-theme-border mx-0.5 self-stretch"></div>
      <ToolBtn
        :active="editor.isActive('blockquote')"
        title="Blockquote"
        @click="editor.chain().focus().toggleBlockquote().run()"
      >
        <SvgIcon type="mdi" :path="mdiFormatQuoteClose" size="1.1em" />
      </ToolBtn>
      <ToolBtn
        :active="editor.isActive('codeBlock')"
        title="Code Block"
        @click="editor.chain().focus().toggleCodeBlock().run()"
      >
        <SvgIcon type="mdi" :path="mdiCodeBlockBraces" size="1.1em" />
      </ToolBtn>
    </div>

    <!-- Editor content -->
    <EditorContent :editor="editor" class="tiptap-content flex-1 overflow-auto" />
  </div>
</template>

<script setup>
import {
  mdiCodeBlockBraces,
  mdiCodeTags,
  mdiFormatBold,
  mdiFormatHeader1,
  mdiFormatHeader2,
  mdiFormatHeader3,
  mdiFormatItalic,
  mdiFormatListBulleted,
  mdiFormatListCheckbox,
  mdiFormatListNumbered,
  mdiFormatQuoteClose,
  mdiFormatStrikethrough,
} from "@mdi/js";
import Collaboration from "@tiptap/extension-collaboration";
import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import TaskItem from "@tiptap/extension-task-item";
import TaskList from "@tiptap/extension-task-list";
import StarterKit from "@tiptap/starter-kit";
import { EditorContent, useEditor } from "@tiptap/vue-3";
import SvgIcon from "@jamescoyle/vue-icon";
import { Markdown } from "tiptap-markdown";
import { defineComponent, onBeforeUnmount, ref, watchEffect } from "vue";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";

import { updateNote } from "../../api.js";
import { getStoredToken } from "../../tokenStorage.js";

const props = defineProps({
  title: { type: String, required: true },
  initialContent: { type: String, default: "" },
});

const emit = defineEmits(["saving", "saved", "error"]);

// Inline toolbar button component
const ToolBtn = defineComponent({
  props: { active: Boolean },
  emits: ["click"],
  template: `
    <button
      class="rounded px-1.5 py-1 transition-colors"
      :class="active
        ? 'bg-theme-brand/20 text-theme-brand'
        : 'text-theme-text-muted hover:bg-theme-background-elevated'"
      @mousedown.prevent="$emit('click')"
    ><slot /></button>
  `,
});

// --- Yjs + WebSocket setup ---
const ydoc = new Y.Doc();
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsBase = `${protocol}//${window.location.host}`;
const token = getStoredToken();
const wsProvider = new WebsocketProvider(
  `${wsBase}/api/ws/notes`,
  encodeURIComponent(props.title),
  ydoc,
  { params: token ? { token } : {} },
);

// --- Reactive state for init coordination ---
const editorReady = ref(false);
const docSynced = ref(false);
let hasInitialized = false;
let autoSaveTimer = null;

// --- Tiptap editor ---
const editor = useEditor({
  extensions: [
    StarterKit.configure({ history: false }),
    Collaboration.configure({ document: ydoc }),
    Markdown.configure({ html: false }),
    TaskList,
    TaskItem.configure({ nested: true }),
    Link.configure({ openOnClick: false, autolink: true }),
    Placeholder.configure({ placeholder: "Start writing…" }),
  ],
  editorProps: {
    attributes: {
      class: "tiptap-inner focus:outline-none",
      spellcheck: "true",
    },
  },
  onUpdate: scheduleAutoSave,
  onCreate: () => {
    editorReady.value = true;
  },
});

// When synced, mark it
wsProvider.on("synced", (isSynced) => {
  if (isSynced) docSynced.value = true;
});

// Once both editor + doc are ready, initialize content if empty
watchEffect(() => {
  if (!editorReady.value || !docSynced.value || hasInitialized || !editor.value) return;
  hasInitialized = true;
  const currentMarkdown = editor.value.storage.markdown.getMarkdown().trim();
  if (!currentMarkdown && props.initialContent) {
    editor.value.commands.setContent(props.initialContent);
  }
});

// --- Auto-save ---
function scheduleAutoSave() {
  clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(doAutoSave, 3000);
}

async function doAutoSave() {
  if (!editor.value) return;
  const markdown = editor.value.storage.markdown.getMarkdown();
  emit("saving");
  try {
    await updateNote(props.title, null, markdown);
    emit("saved");
  } catch {
    emit("error");
  }
}

onBeforeUnmount(() => {
  clearTimeout(autoSaveTimer);
  // Best-effort final save
  if (editor.value) {
    updateNote(props.title, null, editor.value.storage.markdown.getMarkdown()).catch(() => {});
  }
  wsProvider.destroy();
  editor.value?.destroy();
  ydoc.destroy();
});
</script>

<style>
/* Editor typography — matches existing app theme */
.tiptap-inner {
  font-family: "Poppins", sans-serif;
  font-size: 1rem;
  color: rgb(var(--theme-text));
  min-height: 100%;
  padding-bottom: 4rem;
}

.tiptap-inner p {
  line-height: 1.6rem;
  margin: 0 0 0.75rem 0;
}

.tiptap-inner h1,
.tiptap-inner h2,
.tiptap-inner h3,
.tiptap-inner h4,
.tiptap-inner h5,
.tiptap-inner h6 {
  font-weight: bold;
  line-height: 1.4;
  margin: 1em 0 0.5em 0;
  color: rgb(var(--theme-text));
}

.tiptap-inner h1 { font-size: 1.75rem; }
.tiptap-inner h2 { font-size: 1.5rem; }
.tiptap-inner h3 { font-size: 1.25rem; }

.tiptap-inner ul,
.tiptap-inner ol {
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
  color: rgb(var(--theme-text));
}

.tiptap-inner ul { list-style-type: disc; }
.tiptap-inner ol { list-style-type: decimal; }

.tiptap-inner li { margin-bottom: 0.25rem; }

/* Task list */
.tiptap-inner ul[data-type="taskList"] {
  list-style: none;
  padding-left: 0;
}

.tiptap-inner ul[data-type="taskList"] li {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.tiptap-inner ul[data-type="taskList"] li > label {
  flex-shrink: 0;
  margin-top: 0.15rem;
  cursor: pointer;
}

.tiptap-inner ul[data-type="taskList"] li > div {
  flex: 1;
}

.tiptap-inner ul[data-type="taskList"] li[data-checked="true"] > div {
  text-decoration: line-through;
  color: rgb(var(--theme-text-muted));
}

/* Inline code */
.tiptap-inner code {
  font-family: Consolas, "Lucida Console", Monaco, monospace;
  font-size: 0.875em;
  background-color: rgb(var(--theme-background-elevated));
  border-radius: 0.2em;
  padding: 0.1em 0.3em;
}

/* Code block */
.tiptap-inner pre {
  font-family: Consolas, "Lucida Console", Monaco, monospace;
  font-size: 0.875em;
  background-color: rgb(var(--theme-background-elevated));
  border-radius: 0.4rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  overflow-x: auto;
}

.tiptap-inner pre code {
  background: none;
  padding: 0;
  font-size: 1em;
}

/* Blockquote */
.tiptap-inner blockquote {
  border-left: 3px solid rgb(var(--theme-border));
  padding-left: 1rem;
  color: rgb(var(--theme-text-muted));
  margin-bottom: 0.75rem;
}

/* Links */
.tiptap-inner a {
  color: rgb(var(--theme-brand));
  text-decoration: underline;
}

/* HR */
.tiptap-inner hr {
  border: none;
  border-top: 1px solid rgb(var(--theme-border));
  margin: 1rem 0;
}

/* Placeholder */
.tiptap-inner .is-editor-empty:first-child::before {
  color: rgb(var(--theme-text-very-muted));
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
