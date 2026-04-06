<template>
  <nav class="flex items-center justify-between border-b border-theme-border px-3 py-2 print:hidden">
    <!-- Left: sidebar toggle + logo -->
    <div class="flex items-center gap-2">
      <button
        class="rounded p-1 text-theme-text-muted hover:bg-theme-background-elevated"
        title="Toggle sidebar"
        @click="$emit('toggleSidebar')"
      >
        <SvgIcon type="mdi" :path="mdiMenu" size="1.25em" />
      </button>
      <RouterLink :to="{ name: 'home' }">
        <Logo responsive />
      </RouterLink>
    </div>

    <!-- Right: search + menu -->
    <div class="flex items-center gap-1">
      <button
        class="rounded px-2 py-1 text-sm text-theme-text-muted hover:bg-theme-background-elevated"
        title="Search  (/)"
        @click="$emit('toggleSearchModal')"
      >
        <SvgIcon type="mdi" :path="mdiMagnify" size="1.25em" />
      </button>
      <CustomButton :iconPath="mdilMenu" label="Menu" @click="toggleMenu" />
      <PrimeMenu ref="menu" :model="menuItems" :popup="true" />
    </div>
  </nav>
</template>

<script setup>
import { mdiMagnify, mdiMenu } from "@mdi/js";
import { mdilLogout, mdilMenu, mdilMonitor, mdilNoteMultiple } from "@mdi/light-js";
import SvgIcon from "@jamescoyle/vue-icon";
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import CustomButton from "../components/CustomButton.vue";
import Logo from "../components/Logo.vue";
import PrimeMenu from "../components/PrimeMenu.vue";
import { authTypes, params, searchSortOptions } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { toggleTheme } from "../helpers.js";
import { clearStoredToken } from "../tokenStorage.js";

const globalStore = useGlobalStore();
const menu = ref();
const router = useRouter();

defineProps({
  sidebarOpen: Boolean,
});

const emit = defineEmits(["toggleSearchModal", "toggleSidebar"]);

const menuItems = [
  {
    label: "Search",
    icon: mdilNoteMultiple,
    command: () => emit("toggleSearchModal"),
    keyboardShortcut: "/",
  },
  {
    label: "All Notes",
    icon: mdilNoteMultiple,
    command: () =>
      router.push({
        name: "search",
        query: {
          [params.searchTerm]: "*",
          [params.sortBy]: searchSortOptions.title,
        },
      }),
  },
  {
    label: "Toggle Theme",
    icon: mdilMonitor,
    command: toggleTheme,
  },
  {
    separator: true,
    visible: showLogOutButton,
  },
  {
    label: "Log Out",
    icon: mdilLogout,
    command: logOut,
    visible: showLogOutButton,
  },
];

function logOut() {
  clearStoredToken();
  localStorage.clear();
  router.push({ name: "login" });
}

function toggleMenu(event) {
  menu.value.toggle(event);
}

function showLogOutButton() {
  return ![authTypes.none, authTypes.readOnly].includes(
    globalStore.config.authType,
  );
}
</script>
