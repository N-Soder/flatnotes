<template>
  <aside
    class="flex flex-col border-r border-theme-border bg-theme-background transition-all duration-200 print:hidden"
    :class="isOpen ? 'w-56' : 'w-10'"
  >
    <!-- Toggle button row -->
    <div class="flex items-center px-2 py-3" :class="isOpen ? 'justify-between' : 'justify-center'">
      <button
        class="rounded p-1 text-theme-text-muted hover:bg-theme-background-elevated"
        :title="isOpen ? 'Collapse sidebar' : 'Expand sidebar'"
        @click="$emit('toggle')"
      >
        <SvgIcon type="mdi" :path="isOpen ? mdiChevronLeft : mdiChevronRight" size="1.25em" />
      </button>

      <!-- New Note button (shown when expanded) -->
      <button
        v-if="isOpen && canCreate"
        class="rounded p-1 text-theme-text-muted hover:bg-theme-background-elevated"
        title="New Note"
        @click="createNewNote"
      >
        <SvgIcon type="mdi" :path="mdiPlus" size="1.25em" />
      </button>
    </div>

    <!-- Note list (shown when expanded) -->
    <div v-if="isOpen" class="flex-1 overflow-y-auto">
      <!-- Notes -->
      <div v-for="note in notes" :key="note.title">
        <RouterLink
          :to="{ name: 'note', params: { title: note.title } }"
          class="block truncate px-3 py-1.5 text-sm hover:bg-theme-background-elevated"
          :class="isActive(note.title) ? 'bg-theme-background-elevated font-semibold text-theme-text' : 'text-theme-text-muted'"
          :title="note.title"
        >{{ note.title }}</RouterLink>
      </div>

      <!-- Empty state -->
      <p v-if="notes.length === 0" class="px-3 py-2 text-xs text-theme-text-very-muted">
        No notes yet
      </p>
    </div>
  </aside>
</template>

<script setup>
import { mdiChevronLeft, mdiChevronRight, mdiPlus } from "@mdi/js";
import SvgIcon from "@jamescoyle/vue-icon";
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";

import { apiErrorHandler, createNote, getNotes } from "../api.js";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";

const props = defineProps({
  isOpen: { type: Boolean, default: true },
});

defineEmits(["toggle"]);

const globalStore = useGlobalStore();
const route = useRoute();
const router = useRouter();
const toast = useToast();
const notes = ref([]);

const canCreate = computed(
  () => globalStore.config.authType !== authTypes.readOnly,
);

function isActive(title) {
  return route.params?.title === title;
}

async function loadNotes() {
  try {
    notes.value = await getNotes("*", "lastModified", "desc", 100);
  } catch {
    // Silently ignore sidebar load errors
  }
}

async function createNewNote() {
  const base = `Note ${new Date().toISOString().slice(0, 10)}`;
  let title = base;
  let counter = 2;
  while (true) {
    try {
      await createNote(title, "");
      await loadNotes();
      router.push({ name: "note", params: { title } });
      return;
    } catch (error) {
      if (error.response?.status === 409) {
        title = `${base} ${counter++}`;
      } else {
        apiErrorHandler(error, toast);
        return;
      }
    }
  }
}

// Refresh note list when the route changes (e.g., after rename or delete)
watch(
  () => route.params?.title,
  () => loadNotes(),
);

onMounted(loadNotes);
</script>
