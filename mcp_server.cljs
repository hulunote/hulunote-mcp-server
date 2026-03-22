(ns hulunote.mcp-server
  "Hulunote MCP Server - ClojureScript implementation
   Provides note CRUD tools via Model Context Protocol over stdio."
  (:require ["@modelcontextprotocol/sdk/server/mcp.js" :refer [McpServer]]
            ["@modelcontextprotocol/sdk/server/stdio.js" :refer [StdioServerTransport]]
            ["zod" :refer [z]]
            ["https" :as https]
            ["http" :as http]))

;; ==================== Configuration ====================

(def api-token
  (or (.. js/process -env -HULUNOTE_API_TOKEN) ""))

(def api-base
  (or (.. js/process -env -HULUNOTE_API_BASE) "https://www.hulunote.top"))

(def user-agent
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")

;; ==================== HTTP Client ====================

(defn make-hulunote-request
  "POST JSON to Hulunote API endpoint. Returns a JS Promise resolving to parsed JSON."
  [endpoint data]
  (js/Promise.
    (fn [resolve _reject]
      (let [body       (.stringify js/JSON (clj->js data))
            url-obj    (js/URL. (str api-base endpoint))
            protocol   (if (= (.-protocol url-obj) "https:") https http)
            options    #js {:hostname (.-hostname url-obj)
                            :port     (.-port url-obj)
                            :path     (str (.-pathname url-obj) (.-search url-obj))
                            :method   "POST"
                            :headers  #js {"Content-Type"        "application/json"
                                           "Content-Length"      (js/Buffer.byteLength body)
                                           "User-Agent"          user-agent
                                           "X-Functor-Api-Token" api-token
                                           "Referer"             "https://www.hulunote.top/"}}]
        (let [req (.request protocol options
                    (fn [res]
                      (let [chunks #js []]
                        (.on res "data" (fn [chunk] (.push chunks chunk)))
                        (.on res "end"
                          (fn []
                            (let [raw-body (.join chunks "")]
                              (try
                                (let [parsed (.parse js/JSON raw-body)]
                                  (resolve parsed))
                                (catch :default e
                                  (resolve #js {:error true
                                                :message (str "JSON parse error: " (.-message e))})))))))))]
          (.on req "error"
            (fn [e]
              (resolve #js {:error true
                            :message (str "HTTP error: " (.-message e))})))
          (.write req body)
          (.end req))))))

;; ==================== Helpers ====================

(defn format-note
  "Format a note object into a readable string.
   API returns fields prefixed with 'hulunote-notes/'."
  [note]
  (let [f (fn [k] (or (aget note (str "hulunote-notes/" k)) "Unknown"))]
    (str "\nTitle: "       (f "title")
         "\nNote ID: "     (f "id")
         "\nDatabase ID: " (f "database-id")
         "\nRoot Nav ID: " (f "root-nav-id")
         "\nCreated: "     (f "created-at")
         "\n")))

(defn format-nav
  "Format a nav node. API returns flat fields: id, parid, content, etc."
  [node]
  (str "Nav ID: "   (or (aget node "id") "Unknown")
       "\nContent: " (or (aget node "content") "")
       "\nParent: "  (or (aget node "parid") "Root")
       "\nOrder: "   (or (aget node "same-deep-order") 0)))

(defn text-result
  "Wrap text in MCP tool result format."
  [text]
  #js {:content #js [#js {:type "text" :text text}]})

;; ==================== MCP Server ====================

(def server
  (McpServer. #js {:name "hulunote" :version "1.0.0"}))

;; --- Tool: create_note ---
(.tool server
  "create_note"
  "Create a new note in Hulunote. Returns note ID and root-nav-id needed for adding outline nodes."
  #js {:database_name (.describe (.string z) "Name of the database to create the note in")
       :title         (.describe (.string z) "Title of the new note")}
  (fn [params]
    (-> (make-hulunote-request "/hulunote/new-note"
          {:database-name (.-database_name params)
           :title         (.-title params)})
        (.then (fn [result]
                 (if (.-error result)
                   (text-result (str "Failed to create note: " (.-message result)))
                   (text-result (str "Successfully created note!" (format-note result)))))))))

;; --- Tool: get_notes ---
(.tool server
  "get_notes"
  "Get a paginated list of notes from a database"
  #js {:database_id (.describe (.string z) "UUID of the database")
       :page        (.describe (.optional (.number z)) "Page number (default: 1)")
       :page_size   (.describe (.optional (.number z)) "Number of notes per page (default: 20)")}
  (fn [params]
    (-> (make-hulunote-request "/hulunote/get-note-list"
          {:database-id (.-database_id params)
           :page        (or (.-page params) 1)
           :page-size   (or (.-page_size params) 20)})
        (.then (fn [result]
                 (if (.-error result)
                   (text-result (str "Failed to fetch notes: " (.-message result)))
                   (let [notes (or (aget result "note-list") #js [])]
                     (if (zero? (.-length notes))
                       (text-result (str "No notes found on page " (or (.-page params) 1)))
                       (let [all-pages (or (aget result "all-pages") 1)
                             formatted (.map notes format-note)]
                         (text-result
                           (str "Notes (Page " (or (.-page params) 1) ", Pages: " all-pages ")\n"
                                "============================================================\n"
                                (.join formatted "\n---\n"))))))))))))

;; --- Tool: get_all_notes ---
(.tool server
  "get_all_notes"
  "Get all notes from a database (not paginated)"
  #js {:database_id (.describe (.string z) "UUID of the database")}
  (fn [params]
    (-> (make-hulunote-request "/hulunote/get-all-note-list"
          {:database-id (.-database_id params)})
        (.then (fn [result]
                 (if (.-error result)
                   (text-result (str "Failed to fetch notes: " (.-message result)))
                   (let [notes (or (aget result "note-list") #js [])]
                     (if (zero? (.-length notes))
                       (text-result "No notes found in this database")
                       (let [formatted (.map notes format-note)]
                         (text-result
                           (str "All Notes (Total: " (.-length notes) ")\n"
                                "============================================================\n"
                                (.join formatted "\n---\n"))))))))))))

;; --- Tool: update_note ---
(.tool server
  "update_note"
  "Update a note's title and/or content"
  #js {:note_id (.describe (.string z) "UUID of the note to update")
       :title   (.describe (.optional (.string z)) "New title (optional)")
       :content (.describe (.optional (.string z)) "New content (optional)")}
  (fn [params]
    (let [title   (.-title params)
          content (.-content params)]
      (if (and (not title) (not content))
        (js/Promise.resolve
          (text-result "Please provide at least a title or content to update"))
        (let [data (cond-> {:note-id (.-note_id params)}
                     title   (assoc :title title)
                     content (assoc :content content))]
          (-> (make-hulunote-request "/hulunote/update-hulunote-note" data)
              (.then (fn [result]
                       (if (.-error result)
                         (text-result (str "Failed to update note: " (.-message result)))
                         (let [updates (cond-> []
                                         title   (conj (str "Title: " title))
                                         content (conj "Content updated"))]
                           (text-result
                             (str "Successfully updated note " (.-note_id params) "\n"
                                  (.join (clj->js updates) "\n")))))))))))))

;; --- Tool: create_or_update_nav ---
(.tool server
  "create_or_update_nav"
  "Create or update a navigation node in a note's outline. Use parid to set the parent node (use root-nav-id from create_note for top-level items)."
  #js {:note_id  (.describe (.string z) "UUID of the note")
       :id       (.describe (.string z) "UUID for this navigation node (generate a new UUID v4 for new nodes)")
       :content  (.describe (.optional (.string z)) "Text content of the outline node (default: empty)")
       :parid    (.describe (.optional (.string z)) "UUID of the parent node. Use root-nav-id for top-level items.")
       :order    (.describe (.optional (.number z)) "Sort order among siblings (default: 0)")}
  (fn [params]
    (-> (make-hulunote-request "/hulunote/create-or-update-nav"
          (cond-> {:note-id (.-note_id params)
                   :id      (.-id params)
                   :content (or (.-content params) "")
                   :order   (or (.-order params) 0)}
            (.-parid params) (assoc :parid (.-parid params))))
        (.then (fn [result]
                 (if (.-error result)
                   (text-result (str "Failed to create/update nav: " (.-message result)))
                   (let [parid       (.-parid params)
                         parent-info (if parid (str "under parent " parid) "at root level")]
                     (text-result
                       (str "Successfully created/updated nav node "
                            (.-id params) " " parent-info
                            "\nContent: " (or (.-content params) ""))))))))))

;; --- Tool: get_note_navigation ---
(.tool server
  "get_note_navigation"
  "Get all navigation nodes for a note's outline"
  #js {:note_id (.describe (.string z) "UUID of the note")}
  (fn [params]
    (-> (make-hulunote-request "/hulunote/get-note-navs"
          {:note-id (.-note_id params)})
        (.then (fn [result]
                 (if (.-error result)
                   (text-result (str "Failed to fetch nav nodes: " (.-message result)))
                   (let [nodes (or (aget result "nav-list") #js [])]
                     (if (zero? (.-length nodes))
                       (text-result (str "No nav nodes found for note " (.-note_id params)))
                       (let [formatted (.map nodes format-nav)]
                         (text-result
                           (str "Outline for Note " (.-note_id params)
                                " (Total: " (.-length nodes) ")\n"
                                "============================================================\n"
                                (.join formatted "\n---\n"))))))))))))

;; --- Tool: get_all_navigation_nodes ---
(.tool server
  "get_all_navigation_nodes"
  "Get all navigation nodes from a database (paginated)"
  #js {:database_id (.describe (.string z) "UUID of the database")
       :page        (.describe (.optional (.number z)) "Page number (default: 1)")
       :page_size   (.describe (.optional (.number z)) "Number of nodes per page (default: 100)")}
  (fn [params]
    (-> (make-hulunote-request "/hulunote/get-all-nav-by-page"
          {:database-id (.-database_id params)
           :page        (or (.-page params) 1)
           :page-size   (or (.-page_size params) 100)})
        (.then (fn [result]
                 (if (.-error result)
                   (text-result (str "Failed to fetch nav nodes: " (.-message result)))
                   (let [nodes (or (aget result "nav-list") #js [])]
                     (if (zero? (.-length nodes))
                       (text-result (str "No nav nodes found on page " (or (.-page params) 1)))
                       (let [all-pages (or (aget result "all-pages") 1)
                             formatted (.map nodes format-nav)]
                         (text-result
                           (str "Nav Nodes (Page " (or (.-page params) 1)
                                ", Pages: " all-pages ")\n"
                                "============================================================\n"
                                (.join formatted "\n---\n"))))))))))))

;; ==================== Entry Point ====================

(defn main
  "Start the MCP server with stdio transport."
  []
  (let [transport (StdioServerTransport.)]
    (-> (.connect server transport)
        (.then (fn []
                 (.error js/console "Hulunote MCP Server running on stdio"))))))
