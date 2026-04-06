<template>
  <LoadingIndicator ref="loadingIndicator" class="flex h-screen flex-col">
    <PrimeToast />
    <SearchModal v-model="isSearchModalVisible" />

    <!-- Top nav -->
    <NavBar
      v-if="showNavBar"
      :class="{ 'print:hidden': route.name === 'note' }"
      :sidebarOpen="sidebarOpen"
      @toggleSearchModal="toggleSearchModal"
      @toggleSidebar="toggleSidebar"
    />

    <!-- Body: sidebar + content -->
    <div class="flex flex-1 overflow-hidden">
      <Sidebar
        v-if="showNavBar"
        :isOpen="sidebarOpen"
        @toggle="toggleSidebar"
      />

      <!-- Main content -->
      <div class="flex-1 overflow-auto">
        <RouterView />
      </div>
    </div>
  </LoadingIndicator>
</template>

<script setup>
import Mousetrap from "mousetrap";
import "mousetrap/plugins/global-bind/mousetrap-global-bind";
import { useToast } from "primevue/usetoast";
import { computed, ref } from "vue";
import { RouterView, useRoute } from "vue-router";

import { apiErrorHandler, getConfig } from "./api.js";
import PrimeToast from "./components/PrimeToast.vue";
import Sidebar from "./components/Sidebar.vue";
import { useGlobalStore } from "./globalStore.js";
import { loadTheme } from "./helpers.js";
import NavBar from "./partials/NavBar.vue";
import SearchModal from "./partials/SearchModal.vue";
import LoadingIndicator from "./components/LoadingIndicator.vue";
import router from "./router.js";

const globalStore = useGlobalStore();
const isSearchModalVisible = ref(false);
const loadingIndicator = ref();
const route = useRoute();
const toast = useToast();

// Sidebar open/closed — persisted in localStorage
const sidebarOpen = ref(localStorage.getItem("sidebarOpen") !== "false");

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
  localStorage.setItem("sidebarOpen", sidebarOpen.value);
}

// '/' to search
Mousetrap.bind("/", () => {
  if (route.name !== "login") {
    toggleSearchModal();
    return false;
  }
});

// 'CTRL + ALT/OPT + H' to go to home
Mousetrap.bindGlobal("ctrl+alt+h", () => {
  if (route.name !== "login") {
    router.push({ name: "home" });
    return false;
  }
});

getConfig()
  .then((data) => {
    globalStore.config = data;
    loadingIndicator.value.setLoaded();
  })
  .catch((error) => {
    apiErrorHandler(error, toast);
    loadingIndicator.value.setFailed();
  });

const showNavBar = computed(() => route.name !== "login");

function toggleSearchModal() {
  isSearchModalVisible.value = !isSearchModalVisible.value;
}

loadTheme();
</script>
