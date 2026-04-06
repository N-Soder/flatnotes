<template>
  <!-- Blank while redirecting; the router handles navigation immediately -->
</template>

<script setup>
import { useToast } from "primevue/usetoast";
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getNotes } from "../api.js";

const router = useRouter();
const toast = useToast();

onMounted(async () => {
  try {
    const notes = await getNotes("*", "lastModified", "desc", 1);
    if (notes.length) {
      router.replace({ name: "note", params: { title: notes[0].title } });
    } else {
      // No notes yet — go to new note
      router.replace({ name: "new" });
    }
  } catch (error) {
    apiErrorHandler(error, toast);
  }
});
</script>
