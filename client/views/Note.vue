<template>
  <!-- Confirm Deletion Modal -->
  <ConfirmModal
    v-model="isDeleteModalVisible"
    title="Confirm Deletion"
    :message="`Are you sure you want to delete the note '${note.title}'?`"
    confirmButtonText="Delete"
    confirmButtonStyle="danger"
    @confirm="deleteConfirmedHandler"
  />

  <LoadingIndicator ref="loadingIndicator" class="flex h-full flex-col px-2 py-4 md:px-6">
    <!-- Header -->
    <div class="mb-3 flex items-baseline gap-2 print:hidden">
      <!-- Title (inline editable) -->
      <div class="flex-1 min-w-0">
        <span
          v-if="!isTitleEditing"
          class="block truncate text-3xl leading-[1.6em] cursor-text"
          :title="note.title"
          @click="startTitleEdit"
        >{{ note.title }}</span>
        <input
          v-else
          ref="titleInput"
          v-model.trim="editingTitle"
          class="w-full bg-theme-background text-3xl leading-[1.6em] outline-none"
          placeholder="Title"
          @blur="saveTitleEdit"
          @keydown.enter.prevent="saveTitleEdit"
          @keydown.escape.prevent="cancelTitleEdit"
        />
      </div>

      <!-- Right buttons -->
      <div class="flex shrink-0 items-center gap-1">
        <!-- Auto-save status -->
        <span
          class="text-xs"
          :class="{
            'text-theme-text-very-muted': saveStatus === 'saved' || saveStatus === 'idle',
            'text-theme-text-muted': saveStatus === 'saving',
            'text-theme-danger': saveStatus === 'error',
          }"
        >{{ saveStatusText }}</span>
        <!-- Delete -->
        <CustomButton
          v-if="canModify && !isNewNote"
          label="Delete"
          :iconPath="mdilDelete"
          @click="deleteHandler"
        />
      </div>
    </div>

    <!-- Editor — only shown when note is loaded -->
    <TiptapEditor
      v-if="noteLoaded && canModify"
      :key="note.title"
      :title="note.title"
      :initialContent="note.content"
      class="flex-1 overflow-hidden"
      @saving="saveStatus = 'saving'"
      @saved="saveStatus = 'saved'"
      @error="saveStatus = 'error'"
    />

    <!-- Read-only view for read_only auth type -->
    <div
      v-else-if="noteLoaded && !canModify"
      class="flex-1 overflow-auto prose-content"
      v-html="renderedContent"
    />
  </LoadingIndicator>
</template>

<script setup>
import { mdiNoteOffOutline } from "@mdi/js";
import { mdilDelete } from "@mdi/light-js";
import { useToast } from "primevue/usetoast";
import { computed, nextTick, ref, watch, onMounted } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, deleteNote, getNote, updateNote } from "../api.js";
import { Note } from "../classes.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import CustomButton from "../components/CustomButton.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import TiptapEditor from "../components/tiptap/TiptapEditor.vue";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { getToastOptions } from "../helpers.js";

const props = defineProps({
  title: String,
});

const canModify = computed(
  () => globalStore.config.authType !== authTypes.readOnly,
);
const globalStore = useGlobalStore();
const isDeleteModalVisible = ref(false);
const isNewNote = computed(() => !props.title);
const isTitleEditing = ref(false);
const editingTitle = ref("");
const loadingIndicator = ref();
const note = ref(new Note());
const noteLoaded = ref(false);
const reservedFilenameCharacters = /[<>:"/\\|?*]/;
const router = useRouter();
const saveStatus = ref("idle");
const titleInput = ref();
const toast = useToast();

const saveStatusText = computed(() => {
  if (saveStatus.value === "saving") return "Saving…";
  if (saveStatus.value === "error") return "Save failed";
  return "";
});

// Minimal read-only HTML render (strips markdown syntax very roughly)
const renderedContent = computed(() => {
  if (!note.value.content) return "";
  // Escape HTML then convert minimal markdown
  const escaped = note.value.content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped.replace(/\n/g, "<br>");
});

function init() {
  if (props.title && props.title === note.value.title) return;
  noteLoaded.value = false;
  saveStatus.value = "idle";
  loadingIndicator.value.setLoading();

  if (props.title) {
    getNote(props.title)
      .then((data) => {
        note.value = data;
        noteLoaded.value = true;
        loadingIndicator.value.setLoaded();
      })
      .catch((error) => {
        if (error.response?.status === 404) {
          loadingIndicator.value.setFailed("Note not found", mdiNoteOffOutline);
        } else {
          loadingIndicator.value.setFailed();
          apiErrorHandler(error, toast);
        }
      });
  } else {
    // New note — navigate to create new
    note.value = new Note();
    noteLoaded.value = true;
    loadingIndicator.value.setLoaded();
  }
}

// Title editing
function startTitleEdit() {
  if (!canModify.value) return;
  editingTitle.value = note.value.title || "";
  isTitleEditing.value = true;
  nextTick(() => titleInput.value?.focus());
}

function cancelTitleEdit() {
  isTitleEditing.value = false;
}

async function saveTitleEdit() {
  isTitleEditing.value = false;
  const newTitle = editingTitle.value.trim();
  if (!newTitle || newTitle === note.value.title) return;

  if (reservedFilenameCharacters.test(newTitle)) {
    toast.add(
      getToastOptions(
        'Due to filename restrictions, the following characters are not allowed: <>:"/\\|?*',
        "Invalid Title",
        "error",
      ),
    );
    return;
  }

  try {
    const updated = await updateNote(note.value.title, newTitle, null);
    note.value = updated;
    router.replace({ name: "note", params: { title: updated.title } });
  } catch (error) {
    if (error.response?.status === 409) {
      toast.add(
        getToastOptions(
          "A note with this title already exists.",
          "Duplicate",
          "error",
        ),
      );
    } else {
      apiErrorHandler(error, toast);
    }
  }
}

// Deletion
function deleteHandler() {
  isDeleteModalVisible.value = true;
}

function deleteConfirmedHandler() {
  deleteNote(note.value.title)
    .then(() => {
      toast.add(getToastOptions("Note deleted ✓", "Success", "success"));
      router.push({ name: "home" });
    })
    .catch((error) => apiErrorHandler(error, toast));
}

watch(() => props.title, init);
onMounted(init);
</script>
